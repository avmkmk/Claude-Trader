import { useState, useRef, useEffect } from 'react'
import { ChevronDown, X } from 'lucide-react'
import { cn } from '@/lib/utils'

interface SearchableSelectProps {
  options: string[]
  value: string
  onChange: (value: string) => void
  placeholder?: string
  className?: string
  error?: boolean
}

export default function SearchableSelect({
  options,
  value,
  onChange,
  placeholder = 'Search or select...',
  className,
  error,
}: SearchableSelectProps) {
  const [isOpen, setIsOpen] = useState(false)
  const [inputValue, setInputValue] = useState(value)
  const [highlightedIndex, setHighlightedIndex] = useState(0)
  const containerRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLInputElement>(null)
  const listRef = useRef<HTMLDivElement>(null)

  const filtered = inputValue
    ? options.filter((o) => o.toLowerCase().includes(inputValue.toLowerCase()))
    : options

  useEffect(() => {
    setInputValue(value)
  }, [value])

  useEffect(() => {
    function handleClickOutside(e: MouseEvent) {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
        setIsOpen(false)
        if (inputValue && filtered.length > 0) {
          const match = filtered.find(o => o.toLowerCase() === inputValue.toLowerCase())
          if (match) {
            setInputValue(match)
            onChange(match)
          }
        }
      }
    }
    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [inputValue, filtered, onChange])

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const val = e.target.value.toUpperCase()
    setInputValue(val)
    setIsOpen(true)
    setHighlightedIndex(0)

    const exactMatch = options.find(o => o === val)
    if (exactMatch) {
      onChange(exactMatch)
    }
  }

  const handleSelect = (option: string) => {
    setInputValue(option)
    onChange(option)
    setIsOpen(false)
    inputRef.current?.blur()
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (!isOpen) {
      if (e.key === 'ArrowDown' || e.key === 'Enter') {
        setIsOpen(true)
        return
      }
    }

    switch (e.key) {
      case 'ArrowDown':
        e.preventDefault()
        setHighlightedIndex(prev => Math.min(prev + 1, Math.min(filtered.length - 1, 199)))
        break
      case 'ArrowUp':
        e.preventDefault()
        setHighlightedIndex(prev => Math.max(prev - 1, 0))
        break
      case 'Enter':
        e.preventDefault()
        if (filtered[highlightedIndex]) {
          handleSelect(filtered[highlightedIndex])
        }
        break
      case 'Escape':
        setIsOpen(false)
        break
    }
  }

  useEffect(() => {
    if (listRef.current) {
      const item = listRef.current.children[highlightedIndex] as HTMLElement
      item?.scrollIntoView({ block: 'nearest' })
    }
  }, [highlightedIndex])

  return (
    <div ref={containerRef} className={cn('relative', className)}>
      <div className="relative flex items-center">
        <input
          ref={inputRef}
          type="text"
          value={inputValue}
          onChange={handleInputChange}
          onFocus={() => setIsOpen(true)}
          onKeyDown={handleKeyDown}
          placeholder={placeholder}
          className={cn(
            'flex h-10 w-full rounded-md border bg-background px-3 py-2 pr-8 text-sm outline-none placeholder:text-muted-foreground',
            error ? 'border-loss' : 'border-input focus-visible:ring-1 focus-visible:ring-ring'
          )}
        />
        <div className="absolute right-2 flex items-center gap-1">
          {inputValue ? (
            <button
              type="button"
              onClick={(e) => {
                e.stopPropagation()
                setInputValue('')
                onChange('')
                inputRef.current?.focus()
              }}
              className="rounded p-0.5 hover:bg-secondary text-muted-foreground"
            >
              <X size={14} />
            </button>
          ) : (
            <ChevronDown size={14} className="text-muted-foreground" />
          )}
        </div>
      </div>

      {isOpen && filtered.length > 0 && (
        <div
          ref={listRef}
          className="absolute z-50 mt-1 w-full max-h-60 overflow-y-auto rounded-md border border-border bg-card shadow-lg"
        >
          {filtered.slice(0, 200).map((option, idx) => (
            <button
              key={option}
              type="button"
              onClick={() => handleSelect(option)}
              onMouseEnter={() => setHighlightedIndex(idx)}
              className={cn(
                'flex w-full items-center px-3 py-2 text-sm text-left',
                idx === highlightedIndex ? 'bg-primary/10 text-primary' : 'hover:bg-secondary',
                option === value && 'font-medium'
              )}
            >
              {option}
            </button>
          ))}
          {filtered.length > 200 && (
            <div className="px-3 py-1 text-xs text-muted-foreground border-t border-border">
              Showing 200 of {filtered.length}. Type to narrow.
            </div>
          )}
        </div>
      )}

      {isOpen && filtered.length === 0 && inputValue && (
        <div className="absolute z-50 mt-1 w-full rounded-md border border-border bg-card px-3 py-2 text-sm text-muted-foreground shadow-lg">
          No matching symbols
        </div>
      )}
    </div>
  )
}
