# Streamlit UI Authentication Design

**Date:** 2026-03-26
**Status:** Approved
**Implementation Approach:** Runtime Environment Variables

## Problem Statement

The current Streamlit authentication page reads Nubra API credentials from the `.env` file, but the authentication flow requires interactive inputs (phone number, OTP) that are being prompted in the terminal. This creates a poor user experience and security concerns:

1. Sensitive credentials (MPIN, phone, OTP) stored in `.env` file
2. Terminal prompts interrupt the web UI flow
3. No visual feedback during multi-step authentication
4. Users must switch between browser and terminal

## Solution Overview

Move all Nubra authentication to secure Streamlit UI inputs with a two-path authentication flow:
- **Quick Login**: MPIN only (uses existing session token if valid)
- **Full Login**: Phone → OTP → MPIN (three-step sequential flow)

All credentials are provided through the UI, temporarily set as environment variables for SDK initialization, and immediately cleared after use. No credentials persist to disk.

## Architecture

### Components

**1. Streamlit UI (`dashboard/streamlit_app.py`)**
- Modified `auth_page()` function with login type selection
- Multi-step form handling using `st.session_state`
- Progress indicators and error messaging

**2. NubraAPIHandler (`apis/nubra_api.py`)**
- New method: `initialize_sdk_with_credentials(phone, mpin, otp)`
- Temporarily sets environment variables for SDK
- Returns tuple `(success, error_message)` for better error handling

**3. Environment Variables (Runtime Only)**
- `PHONE_NO`, `MPIN`, `OTP` set via `os.environ` during authentication
- Never persisted to `.env` file
- Cleared immediately after SDK initialization (success or failure)

### Data Flow

```
User Input (UI)
    → st.session_state (temporary storage)
    → NubraAPIHandler.initialize_sdk_with_credentials()
    → os.environ (temporary)
    → InitNubraSdk(env_creds=True)
    → Authentication Success/Failure
    → Clear env vars
```

## Detailed Design

### 1. Authentication Flow

#### Login Type Selection (Step 0)

User chooses between two authentication paths:
- **Quick Login (MPIN only)**: For subsequent logins when session token is valid
- **Full Login (Phone/OTP/MPIN)**: For first login of the day or expired tokens

#### Path A: Quick Login

**UI:**
```
Choose Login Method:
○ Quick Login (MPIN only)
● Full Login (Phone/OTP/MPIN)

MPIN: [********]
      [Authenticate]
```

**Flow:**
1. User enters MPIN (password field)
2. Click "Authenticate"
3. Call `initialize_sdk_with_credentials(mpin=user_mpin)`
4. If successful → Show success, store handler in `st.session_state['nubra']`
5. If failed → Show error suggesting Full Login

#### Path B: Full Login (Three Sequential Steps)

**Step 1: Phone Number**
```
Full Login - Step 1 of 3

Phone Number: [__________]
             [Send OTP]
```

**Flow:**
1. User enters 10-digit phone number
2. Validate format (10 digits)
3. Click "Send OTP"
4. Store phone in `st.session_state['phone_number']`
5. Set `st.session_state['auth_step'] = 'otp'`
6. Show success message: "OTP sent to your phone"

**Step 2: OTP Verification**
```
Full Login - Step 2 of 3

OTP sent to: +91-XXXXX-XXX45

Enter OTP: [______]
          [Verify OTP]
```

**Flow:**
1. User enters 6-digit OTP
2. Click "Verify OTP"
3. Call SDK with phone + OTP to verify
4. If valid → Set `st.session_state['otp_verified'] = True`, move to step 3
5. If invalid → Show error, allow retry

**Step 3: MPIN Authentication**
```
Full Login - Step 3 of 3

Enter MPIN: [********]
           [Authenticate]
```

**Flow:**
1. User enters MPIN
2. Click "Authenticate"
3. Call `initialize_sdk_with_credentials(phone, mpin, otp)` with all credentials
4. If successful → Store handler, show success
5. If failed → Show error with retry option

### 2. UI Components

#### State Management (st.session_state)

**Login Flow Tracking:**
```python
st.session_state['login_type'] = 'quick' | 'full'
st.session_state['auth_step'] = 'phone' | 'otp' | 'mpin'
st.session_state['auth_status'] = 'pending' | 'success' | 'failed'
```

**Temporary Credential Storage:**
```python
st.session_state['phone_number'] = str  # After step 1
st.session_state['otp_verified'] = bool  # After step 2
```

**Authenticated Handler:**
```python
st.session_state['nubra'] = NubraAPIHandler  # After success
```

#### Progress Indication

For Full Login, show visual progress:
```
Step 1 of 3: Phone Number
Step 2 of 3: OTP Verification
Step 3 of 3: MPIN Authentication
```

Use Streamlit's native components:
- `st.progress()` for visual progress bar
- Step number in header
- Disabled/completed steps grayed out

#### Input Fields

**Phone Number:**
- Text input, max 10 characters
- Validation: digits only, exactly 10 chars
- Placeholder: "Enter 10-digit mobile number"

**OTP:**
- Text input, max 6 characters
- Type: password (masked)
- Placeholder: "Enter 6-digit OTP"

**MPIN:**
- Text input, type="password"
- Masked input for security
- Placeholder: "Enter your MPIN"

### 3. Backend Implementation

#### NubraAPIHandler Changes

**New Method:**

```python
def initialize_sdk_with_credentials(self, phone=None, mpin=None, otp=None):
    """
    Initialize SDK with credentials from UI instead of .env file.

    Args:
        phone (str, optional): Phone number for full login
        mpin (str, required): MPIN for authentication
        otp (str, optional): OTP code for full login step 2

    Returns:
        tuple: (success: bool, error_message: str or None)

    Example:
        # Quick login
        success, error = handler.initialize_sdk_with_credentials(mpin="1234")

        # Full login
        success, error = handler.initialize_sdk_with_credentials(
            phone="9876543210",
            mpin="1234",
            otp="123456"
        )
    """
    import os

    try:
        # Set environment variables temporarily
        if phone:
            os.environ['PHONE_NO'] = phone
        if mpin:
            os.environ['MPIN'] = mpin
        if otp:
            os.environ['OTP'] = otp

        # Initialize SDK (reads from env vars via env_creds=True)
        self.sdk_instance = InitNubraSdk(self.env, env_creds=True)
        self.market_data_api = MarketData(self.sdk_instance)
        self.trading_api = Trading(self.sdk_instance)

        # Clear sensitive environment variables after initialization
        for key in ['MPIN', 'OTP']:
            if key in os.environ:
                del os.environ[key]

        return (True, None)

    except Exception as e:
        error_msg = str(e)

        # Clear all credentials on failure
        for key in ['PHONE_NO', 'MPIN', 'OTP']:
            if key in os.environ:
                del os.environ[key]

        return (False, error_msg)
```

**Design Decisions:**

1. **Return Tuple**: `(success, error_message)` instead of just bool for better error reporting to UI
2. **Optional Parameters**: Pass only needed credentials (MPIN for quick, all three for full)
3. **Immediate Cleanup**: Delete sensitive env vars after use (success or failure)
4. **Backward Compatibility**: Keep original `initialize_sdk()` method unchanged
5. **Phone Persistence**: Keep `PHONE_NO` in env (less sensitive) but clear MPIN/OTP immediately

### 4. Error Handling

#### Quick Login Errors

**Invalid MPIN:**
```
❌ Authentication failed. Please check your MPIN or try Full Login if your session has expired.
```

**Network Error:**
```
❌ Connection error: [error details]. Please check your internet and try again.
```

#### Full Login Errors

**Step 1 - Phone Number:**

*Invalid Format:*
```
⚠️ Please enter a valid 10-digit phone number
```

*SDK Error:*
```
❌ Failed to send OTP: [error details]
```

**Step 2 - OTP:**

*Invalid OTP:*
```
❌ Invalid OTP. Please check and try again. (Attempts remaining: X)
```

*Expired OTP:*
```
❌ OTP has expired. Please request a new one.
[Resend OTP]
```

*Max Attempts:*
```
❌ Too many failed attempts. Please try again later.
```

**Step 3 - MPIN:**

*Invalid MPIN:*
```
❌ Invalid MPIN. Please try again.
```

*Account Locked:*
```
❌ Account temporarily locked due to multiple failed attempts. Please try again later.
```

#### Error Display Strategy

- Use `st.error()` for authentication failures
- Use `st.warning()` for validation issues
- Use `st.info()` for helpful guidance
- Include actionable next steps in error messages
- Log technical details to console (not displayed to user)

### 5. Security Considerations

#### Credential Handling

**No Disk Persistence:**
- Credentials never written to `.env` file
- No logging of sensitive data (MPIN, OTP)
- No caching of credentials in files

**Memory Management:**
- Environment variables cleared immediately after SDK init
- Session state cleared on app restart
- No credential storage in browser localStorage

**Input Security:**
- MPIN and OTP fields use `type="password"` for masking
- No autocomplete on sensitive fields
- Phone number validation prevents injection

#### Best Practices

**1. HTTPS Enforcement (Production):**
Add warning banner if not using HTTPS:
```
⚠️ Warning: Not using HTTPS. Your credentials may not be secure.
```

**2. Rate Limiting:**
Rely on Nubra SDK's built-in rate limiting for:
- OTP request frequency
- Failed authentication attempts
- API call throttling

**3. Token Management:**
Let Nubra SDK handle:
- Session token storage
- Token expiration
- Token refresh logic

**4. UI Security Tips (Optional Banner):**
```
🔒 Security Tips:
• Never share your MPIN or OTP with anyone
• Ensure you're using HTTPS in production
• Close the app when done to clear authentication
```

#### Threat Mitigation

**Shoulder Surfing:**
- Mitigated by password masking on MPIN/OTP fields

**Session Hijacking:**
- Mitigated by session tokens in SDK (day-limited)
- Recommend HTTPS in production

**Credential Sniffing:**
- Mitigated by no disk persistence
- Environment variables cleared after use

**Brute Force:**
- Mitigated by Nubra SDK rate limiting
- Show error messages about locked accounts

### 6. Implementation Details

#### File Changes

**Modified Files:**
1. `dashboard/streamlit_app.py` - Rewrite `auth_page()` function
2. `apis/nubra_api.py` - Add `initialize_sdk_with_credentials()` method

**No New Files Required**

#### Streamlit Session State Lifecycle

**Initial Load:**
```python
# All state variables uninitialized
st.session_state = {}
```

**After Login Type Selection:**
```python
st.session_state = {
    'login_type': 'quick' | 'full',
    'auth_status': 'pending'
}
```

**During Full Login (Step 1):**
```python
st.session_state = {
    'login_type': 'full',
    'auth_step': 'phone',
    'auth_status': 'pending'
}
```

**After Phone Submission:**
```python
st.session_state = {
    'login_type': 'full',
    'auth_step': 'otp',
    'phone_number': '9876543210',
    'auth_status': 'pending'
}
```

**After OTP Verification:**
```python
st.session_state = {
    'login_type': 'full',
    'auth_step': 'mpin',
    'phone_number': '9876543210',
    'otp_verified': True,
    'auth_status': 'pending'
}
```

**After Successful Authentication:**
```python
st.session_state = {
    'login_type': 'full',
    'auth_step': 'mpin',
    'phone_number': '9876543210',
    'otp_verified': True,
    'auth_status': 'success',
    'nubra': <NubraAPIHandler instance>
}
```

#### State Reset Scenarios

**Back Button:**
```python
# Clear current attempt, return to login type selection
keys_to_clear = ['auth_step', 'phone_number', 'otp_verified']
for key in keys_to_clear:
    if key in st.session_state:
        del st.session_state[key]
```

**Authentication Failure:**
```python
# Clear credentials but keep login type
st.session_state['auth_status'] = 'failed'
# Keep 'login_type' to allow easy retry
```

**Logout (Optional):**
```python
# Clear everything
st.session_state.clear()
```

## Testing Strategy

### Manual Testing Checklist

**Quick Login Path:**
- [ ] Valid MPIN → Success
- [ ] Invalid MPIN → Error message
- [ ] Network error → Appropriate error
- [ ] Token expired → Suggest Full Login

**Full Login Path:**
- [ ] Phone validation (10 digits)
- [ ] OTP sent confirmation message
- [ ] Valid OTP → Proceed to MPIN
- [ ] Invalid OTP → Error with retry
- [ ] Expired OTP → Resend option
- [ ] Valid MPIN after OTP → Success
- [ ] Invalid MPIN → Error

**State Management:**
- [ ] Progress indicator updates correctly
- [ ] Back button resets state properly
- [ ] Session persists across page navigation
- [ ] App restart clears authentication

**Security:**
- [ ] MPIN masked in UI
- [ ] OTP masked in UI
- [ ] No credentials in browser console
- [ ] Environment variables cleared after auth

**Error Handling:**
- [ ] All error types display appropriate messages
- [ ] Error messages are actionable
- [ ] Network errors don't crash app

## Future Enhancements (Out of Scope)

1. **Remember Phone Number**: Store phone number locally (encrypted) for convenience
2. **Biometric Auth**: Integration with browser biometric APIs
3. **Session Timeout Warning**: Notify user before token expires
4. **Logout Button**: Explicit logout to clear session
5. **Multi-Factor Options**: Support for authenticator apps instead of OTP
6. **Rate Limit UI**: Show countdown timer when rate limited
7. **OTP Resend**: Automatic resend OTP button after timer

## Migration Notes

### Updating Existing `.env` File

After implementation, users can optionally remove these from `.env`:
```bash
# These are no longer needed (will be entered via UI)
# NUBRA_CLIENT_ID="I01VI9"  # Not needed at all
# NUBRA_MPIN="4565"         # Now entered in UI
# PHONE_NO="9876543210"     # Now entered in UI
```

Keep only non-authentication credentials:
```bash
# Keep these (if applicable)
UPSTOX_ACCESS_TOKEN="YOUR_UPSTOX_ACCESS_TOKEN"
```

### Backward Compatibility

The original `initialize_sdk()` method remains unchanged, so any scripts or notebooks that import and use it directly will continue to work. Only the Streamlit UI uses the new credential-based initialization.

## Success Metrics

1. **User Experience**: No terminal prompts during Streamlit authentication flow
2. **Security**: No sensitive credentials stored in `.env` file
3. **Reliability**: Clear error messages guide users through authentication issues
4. **Flexibility**: Both quick and full login paths work seamlessly
5. **State Management**: Authentication persists across page navigation in Streamlit app

## Appendix

### Nubra SDK Environment Variables

Based on error messages, the Nubra SDK expects:
- `PHONE_NO`: 10-digit mobile number
- `MPIN`: User's MPIN for authentication
- `OTP`: One-time password (when required)

These are set temporarily via `os.environ` and cleared after use.

### Streamlit UI Components Used

- `st.radio()`: Login type selection
- `st.text_input()`: All credential inputs
- `st.button()`: Submit buttons
- `st.progress()`: Visual progress bar
- `st.error()`: Error messages
- `st.warning()`: Validation warnings
- `st.success()`: Success confirmations
- `st.info()`: Helpful tips
- `st.session_state`: State management
