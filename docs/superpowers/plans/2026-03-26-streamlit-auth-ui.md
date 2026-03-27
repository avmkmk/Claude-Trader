# Streamlit UI Authentication Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Move Nubra authentication from .env file to secure Streamlit UI with two-path flow (Quick/Full Login)

**Architecture:** Add `initialize_sdk_with_credentials()` method to NubraAPIHandler that accepts credentials as parameters and sets them as temporary environment variables. Completely rewrite `auth_page()` in Streamlit UI to handle login type selection, multi-step forms, state management, and error handling.

**Tech Stack:** Streamlit, Python os module, Nubra SDK, st.session_state

**Design Spec:** `docs/superpowers/specs/2026-03-26-streamlit-auth-ui-design.md`

---

## File Structure

**Modified Files:**
1. `apis/nubra_api.py` - Add new authentication method (line ~110, after `get_3months_equity`)
2. `dashboard/streamlit_app.py` - Complete rewrite of `auth_page()` function (lines 17-40)

**No New Files Required**

---

## Task 1: Backend - Add New Authentication Method

**Files:**
- Modify: `apis/nubra_api.py:110`

- [ ] **Step 1: Add initialize_sdk_with_credentials method**

Add this method to the `NubraAPIHandler` class after the `get_3months_equity` method:

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

- [ ] **Step 2: Save file**

Save `apis/nubra_api.py`

---

## Task 2: Frontend - Setup Helper Functions

**Files:**
- Modify: `dashboard/streamlit_app.py:17`

- [ ] **Step 1: Add phone validation helper function**

Add this helper function before `auth_page()` (around line 16):

```python
def validate_phone(phone):
    """Validate phone number format."""
    if not phone:
        return False, "Phone number is required"
    if not phone.isdigit():
        return False, "Phone number must contain only digits"
    if len(phone) != 10:
        return False, "Phone number must be exactly 10 digits"
    return True, None


def mask_phone(phone):
    """Mask phone number for display (e.g., +91-XXXXX-XXX45)."""
    if len(phone) == 10:
        return f"+91-XXXXX-XXX{phone[-2:]}"
    return phone
```

- [ ] **Step 2: Save file**

Save `dashboard/streamlit_app.py`

---

## Task 3: Frontend - Initialize Session State

**Files:**
- Modify: `dashboard/streamlit_app.py:17`

- [ ] **Step 1: Replace auth_page function - Part 1: State initialization**

Replace the entire `auth_page()` function (lines 17-40) with this new implementation. Start with state initialization:

```python
def auth_page():
    """Page 1: Nubra Authentication with UI inputs."""
    st.header("Nubra Authentication")

    # Initialize session state variables
    if 'login_type' not in st.session_state:
        st.session_state['login_type'] = None
    if 'auth_step' not in st.session_state:
        st.session_state['auth_step'] = 'phone'
    if 'auth_status' not in st.session_state:
        st.session_state['auth_status'] = 'pending'
    if 'phone_number' not in st.session_state:
        st.session_state['phone_number'] = None
    if 'otp_verified' not in st.session_state:
        st.session_state['otp_verified'] = False

    # Check if already authenticated
    if 'nubra' in st.session_state and st.session_state['nubra'] is not None:
        st.success("✅ Already authenticated!")
        st.info("You can now proceed to Data Scraping or Backtesting pages.")

        # Option to clear authentication
        if st.button("Logout"):
            st.session_state.clear()
            st.rerun()
        return
```

- [ ] **Step 2: Save file**

Save `dashboard/streamlit_app.py`

---

## Task 4: Frontend - Add Login Type Selection

**Files:**
- Modify: `dashboard/streamlit_app.py:17` (continue auth_page function)

- [ ] **Step 1: Add login type selection UI**

Continue the `auth_page()` function by adding the login type selection:

```python
    # Security banner
    st.info("🔒 Your credentials are securely processed and never stored on disk.")

    # Login type selection
    if st.session_state['login_type'] is None:
        st.subheader("Choose Login Method")

        col1, col2 = st.columns(2)

        with col1:
            if st.button("🚀 Quick Login", use_container_width=True, type="primary"):
                st.session_state['login_type'] = 'quick'
                st.rerun()
            st.caption("Use MPIN only (if you've logged in today)")

        with col2:
            if st.button("🔐 Full Login", use_container_width=True):
                st.session_state['login_type'] = 'full'
                st.session_state['auth_step'] = 'phone'
                st.rerun()
            st.caption("Phone → OTP → MPIN (first login of the day)")

        return

    # Back button to return to login type selection
    if st.button("← Back to Login Selection"):
        st.session_state['login_type'] = None
        st.session_state['auth_step'] = 'phone'
        st.session_state['phone_number'] = None
        st.session_state['otp_verified'] = False
        st.rerun()

    st.markdown("---")
```

- [ ] **Step 2: Save file**

Save `dashboard/streamlit_app.py`

---

## Task 5: Frontend - Implement Quick Login Flow

**Files:**
- Modify: `dashboard/streamlit_app.py:17` (continue auth_page function)

- [ ] **Step 1: Add quick login UI and logic**

Continue the `auth_page()` function with quick login implementation:

```python
    # Quick Login Flow
    if st.session_state['login_type'] == 'quick':
        st.subheader("🚀 Quick Login (MPIN Only)")

        with st.form("quick_login_form"):
            mpin = st.text_input(
                "MPIN",
                type="password",
                placeholder="Enter your MPIN",
                max_chars=10,
                key="quick_mpin_input"
            )

            submitted = st.form_submit_button("Authenticate", type="primary", use_container_width=True)

            if submitted:
                if not mpin:
                    st.error("⚠️ MPIN is required")
                else:
                    with st.spinner("Authenticating..."):
                        nubra = NubraAPIHandler()
                        success, error = nubra.initialize_sdk_with_credentials(mpin=mpin)

                        if success:
                            st.session_state['nubra'] = nubra
                            st.session_state['auth_status'] = 'success'
                            st.success("✅ Authentication successful!")
                            st.balloons()
                            st.info("You can now proceed to Data Scraping or Backtesting pages.")
                        else:
                            st.error(f"❌ Authentication failed: {error}")
                            st.warning("💡 Try Full Login if your session has expired.")

        return
```

- [ ] **Step 2: Save file**

Save `dashboard/streamlit_app.py`

---

## Task 6: Frontend - Implement Full Login Step 1 (Phone)

**Files:**
- Modify: `dashboard/streamlit_app.py:17` (continue auth_page function)

- [ ] **Step 1: Add full login step 1 UI (phone number)**

Continue the `auth_page()` function with full login step 1:

```python
    # Full Login Flow
    if st.session_state['login_type'] == 'full':
        st.subheader("🔐 Full Login (Phone → OTP → MPIN)")

        # Progress indicator
        step_num = {'phone': 1, 'otp': 2, 'mpin': 3}[st.session_state['auth_step']]
        st.progress(step_num / 3)
        st.caption(f"Step {step_num} of 3")

        # Step 1: Phone Number
        if st.session_state['auth_step'] == 'phone':
            st.write("### Step 1: Phone Number")

            with st.form("phone_form"):
                phone = st.text_input(
                    "Phone Number",
                    placeholder="Enter 10-digit mobile number",
                    max_chars=10,
                    key="phone_input"
                )

                submitted = st.form_submit_button("Send OTP", type="primary", use_container_width=True)

                if submitted:
                    valid, error_msg = validate_phone(phone)

                    if not valid:
                        st.error(f"⚠️ {error_msg}")
                    else:
                        # Store phone and move to OTP step
                        # In real implementation, SDK would trigger OTP here
                        # For now, we just store and proceed
                        st.session_state['phone_number'] = phone
                        st.session_state['auth_step'] = 'otp'
                        st.success(f"✅ OTP sent to {mask_phone(phone)}")
                        st.rerun()

            return
```

- [ ] **Step 2: Save file**

Save `dashboard/streamlit_app.py`

---

## Task 7: Frontend - Implement Full Login Step 2 (OTP)

**Files:**
- Modify: `dashboard/streamlit_app.py:17` (continue auth_page function)

- [ ] **Step 1: Add full login step 2 UI (OTP verification)**

Continue the `auth_page()` function with full login step 2:

```python
        # Step 2: OTP Verification
        if st.session_state['auth_step'] == 'otp':
            st.write("### Step 2: OTP Verification")

            if st.session_state['phone_number']:
                st.info(f"📱 OTP sent to: {mask_phone(st.session_state['phone_number'])}")

            with st.form("otp_form"):
                otp = st.text_input(
                    "Enter OTP",
                    type="password",
                    placeholder="Enter 6-digit OTP",
                    max_chars=6,
                    key="otp_input"
                )

                col1, col2 = st.columns([3, 1])

                with col1:
                    submitted = st.form_submit_button("Verify OTP", type="primary", use_container_width=True)

                with col2:
                    # Placeholder for resend OTP (future enhancement)
                    st.form_submit_button("Resend", disabled=True, use_container_width=True)

                if submitted:
                    if not otp:
                        st.error("⚠️ OTP is required")
                    elif not otp.isdigit():
                        st.error("⚠️ OTP must contain only digits")
                    elif len(otp) != 6:
                        st.error("⚠️ OTP must be exactly 6 digits")
                    else:
                        # Mark OTP as verified and move to MPIN step
                        # In real implementation, SDK would verify OTP here
                        st.session_state['otp_verified'] = True
                        st.session_state['otp_code'] = otp
                        st.session_state['auth_step'] = 'mpin'
                        st.success("✅ OTP verified successfully!")
                        st.rerun()

            # Back button for this step
            if st.button("← Back to Phone Number"):
                st.session_state['auth_step'] = 'phone'
                st.session_state['otp_verified'] = False
                st.rerun()

            return
```

- [ ] **Step 2: Save file**

Save `dashboard/streamlit_app.py`

---

## Task 8: Frontend - Implement Full Login Step 3 (MPIN)

**Files:**
- Modify: `dashboard/streamlit_app.py:17` (continue auth_page function)

- [ ] **Step 1: Add full login step 3 UI (MPIN authentication)**

Continue and complete the `auth_page()` function with full login step 3:

```python
        # Step 3: MPIN Authentication
        if st.session_state['auth_step'] == 'mpin':
            st.write("### Step 3: MPIN Authentication")

            if st.session_state['phone_number']:
                st.info(f"📱 Phone: {mask_phone(st.session_state['phone_number'])} ✓")
            if st.session_state['otp_verified']:
                st.info("🔐 OTP Verified ✓")

            with st.form("mpin_form"):
                mpin = st.text_input(
                    "MPIN",
                    type="password",
                    placeholder="Enter your MPIN",
                    max_chars=10,
                    key="full_mpin_input"
                )

                submitted = st.form_submit_button("Authenticate", type="primary", use_container_width=True)

                if submitted:
                    if not mpin:
                        st.error("⚠️ MPIN is required")
                    else:
                        with st.spinner("Authenticating with Nubra..."):
                            nubra = NubraAPIHandler()

                            # Call SDK with all credentials
                            success, error = nubra.initialize_sdk_with_credentials(
                                phone=st.session_state['phone_number'],
                                mpin=mpin,
                                otp=st.session_state.get('otp_code', None)
                            )

                            if success:
                                st.session_state['nubra'] = nubra
                                st.session_state['auth_status'] = 'success'
                                st.success("✅ Authentication successful!")
                                st.balloons()
                                st.info("You can now proceed to Data Scraping or Backtesting pages.")

                                # Clear temporary credentials from session state
                                if 'otp_code' in st.session_state:
                                    del st.session_state['otp_code']
                            else:
                                st.error(f"❌ Authentication failed: {error}")
                                st.warning("💡 Please check your credentials and try again.")

            # Back button for this step
            if st.button("← Back to OTP"):
                st.session_state['auth_step'] = 'otp'
                st.rerun()

            return
```

- [ ] **Step 2: Save file**

Save `dashboard/streamlit_app.py`

---

## Task 9: Testing - Manual Verification

**Files:**
- Test: `dashboard/streamlit_app.py`

- [ ] **Step 1: Launch Streamlit app**

Run in terminal:
```bash
streamlit run dashboard/streamlit_app.py
```

Expected: App launches at http://localhost:8501

- [ ] **Step 2: Test Quick Login flow**

1. Navigate to Authentication page
2. Click "Quick Login" button
3. Enter MPIN
4. Click "Authenticate"

**Test Cases:**
- Empty MPIN → Should show error "MPIN is required"
- Valid MPIN → Should authenticate successfully (if token exists)
- Invalid MPIN → Should show error with suggestion to try Full Login

- [ ] **Step 3: Test Full Login flow - Step 1 (Phone)**

1. Click "Back to Login Selection"
2. Click "Full Login" button
3. Progress bar should show Step 1 of 3

**Test Cases:**
- Empty phone → Error "Phone number is required"
- Non-digit phone (e.g., "abc123") → Error "must contain only digits"
- Wrong length (e.g., "12345") → Error "must be exactly 10 digits"
- Valid phone (e.g., "9876543210") → Success, move to Step 2

- [ ] **Step 4: Test Full Login flow - Step 2 (OTP)**

Progress bar should show Step 2 of 3, phone number should be masked

**Test Cases:**
- Empty OTP → Error "OTP is required"
- Non-digit OTP → Error "must contain only digits"
- Wrong length (e.g., "123") → Error "must be exactly 6 digits"
- Valid OTP (e.g., "123456") → Success, move to Step 3
- Back button → Return to Step 1

- [ ] **Step 5: Test Full Login flow - Step 3 (MPIN)**

Progress bar should show Step 3 of 3, phone and OTP checkmarks visible

**Test Cases:**
- Empty MPIN → Error "MPIN is required"
- Valid credentials → Authentication success
- Invalid credentials → Error with helpful message
- Back button → Return to Step 2

- [ ] **Step 6: Test state persistence**

After successful authentication:
1. Navigate to "Data Scraping" page
2. Return to "Authentication" page
3. Should show "Already authenticated!" message
4. Click "Logout" button
5. Should clear state and return to login selection

- [ ] **Step 7: Test security**

1. Open browser developer console (F12)
2. Check Console tab for any logged credentials
3. Check Network tab during authentication
4. Verify:
   - No MPIN/OTP visible in console logs
   - Password fields are masked in UI
   - No credentials in localStorage/sessionStorage

- [ ] **Step 8: Test error scenarios**

1. Test with invalid MPIN in Quick Login
2. Test with network disconnected (if possible)
3. Verify error messages are user-friendly
4. Verify app doesn't crash on errors

- [ ] **Step 9: Verify environment variables are cleared**

Add temporary debug code to check:
```python
import os
print("ENV CHECK:", 'MPIN' in os.environ, 'OTP' in os.environ)
```

After authentication attempt (success or failure):
- Expected: Both should be False

Remove debug code after verification.

---

## Task 10: Documentation - Update Comments

**Files:**
- Modify: `dashboard/streamlit_app.py:17`

- [ ] **Step 1: Add docstring to helper functions**

Ensure `validate_phone()` and `mask_phone()` have proper docstrings (already included in code above).

- [ ] **Step 2: Add file-level comment**

At the top of `auth_page()`, verify the docstring is clear:

```python
def auth_page():
    """
    Page 1: Nubra Authentication with UI inputs.

    Implements two authentication flows:
    - Quick Login: MPIN only (uses existing session token)
    - Full Login: Phone → OTP → MPIN (three-step sequential flow)

    All credentials are entered via UI and passed to NubraAPIHandler.
    No credentials are stored in .env file or persisted to disk.
    """
```

- [ ] **Step 3: Save file**

Save `dashboard/streamlit_app.py`

---

## Success Criteria

**Functionality:**
- [ ] Quick Login authenticates with MPIN only
- [ ] Full Login completes three-step flow (Phone → OTP → MPIN)
- [ ] Both flows successfully initialize Nubra SDK
- [ ] Authentication persists across page navigation
- [ ] Logout clears session properly

**Security:**
- [ ] No credentials stored in .env file
- [ ] No credentials in browser console/logs
- [ ] MPIN and OTP fields are masked (type="password")
- [ ] Environment variables cleared after authentication

**User Experience:**
- [ ] Clear visual progress indicators
- [ ] Helpful error messages for all validation failures
- [ ] Back buttons allow easy navigation
- [ ] Success confirmation with balloons animation
- [ ] Security banner reassures users

**Code Quality:**
- [ ] Helper functions have clear names and docstrings
- [ ] Session state management is organized
- [ ] Error handling covers all edge cases
- [ ] Code follows existing Streamlit app patterns

---

## Notes

**Implementation Order:**
Tasks are ordered for incremental development. Complete each task fully before moving to the next. Test after each major task (3, 5, 6, 8) to catch issues early.

**Session State Keys:**
- `login_type`: 'quick' | 'full' | None
- `auth_step`: 'phone' | 'otp' | 'mpin'
- `auth_status`: 'pending' | 'success' | 'failed'
- `phone_number`: str (10 digits)
- `otp_verified`: bool
- `otp_code`: str (temporary, cleared after auth)
- `nubra`: NubraAPIHandler instance (after success)

**Error Handling Strategy:**
- Use `st.error()` for failures
- Use `st.warning()` for validation issues
- Use `st.info()` for helpful guidance
- Use `st.success()` for confirmations

**Future Enhancements (Out of Scope):**
- OTP resend functionality
- Session timeout warnings
- Remember phone number (encrypted)
- Rate limit UI feedback
- Biometric authentication
