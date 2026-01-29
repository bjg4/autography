/**
 * Brand icon for Autography - a stylized "A" that represents
 * the autobiographical nature of the knowledge base.
 * Used as chat avatar and can be used as favicon/logo mark.
 */

interface BrandIconProps {
  size?: 'sm' | 'md' | 'lg'
  variant?: 'user' | 'brand'
  className?: string
}

export function BrandIcon({ size = 'md', variant = 'user', className = '' }: BrandIconProps) {
  const sizeClasses = {
    sm: 'w-5 h-5 text-[10px]',
    md: 'w-8 h-8 text-sm',
    lg: 'w-10 h-10 text-base',
  }

  if (variant === 'brand') {
    // Logo mark - stylized A with a pen stroke
    return (
      <div className={`${sizeClasses[size]} rounded-full bg-[#C45A3B] flex items-center justify-center ${className}`}>
        <span className="font-serif italic text-white font-normal" style={{ marginTop: '-1px' }}>
          A
        </span>
      </div>
    )
  }

  // User variant - warm terracotta circle with initial
  return (
    <div className={`${sizeClasses[size]} rounded-full bg-[#C45A3B]/10 flex items-center justify-center flex-shrink-0 ${className}`}>
      <svg
        viewBox="0 0 24 24"
        fill="none"
        className="w-[60%] h-[60%] text-[#C45A3B]"
        aria-hidden="true"
      >
        {/* Stylized quill/pen nib - representing writing/autobiography */}
        <path
          d="M20 4L12 12M12 12L4 20M12 12L8 8M12 12L16 16M7 17C7 17 6 19 4 20C6 20 8 19 8 19"
          stroke="currentColor"
          strokeWidth="1.5"
          strokeLinecap="round"
          strokeLinejoin="round"
        />
      </svg>
    </div>
  )
}

/**
 * Simple user avatar with a cleaner pen/writing icon
 */
export function UserAvatar({ className = '' }: { className?: string }) {
  return (
    <div className={`w-8 h-8 rounded-full bg-[#C45A3B]/10 flex items-center justify-center flex-shrink-0 ${className}`}>
      <svg
        viewBox="0 0 24 24"
        fill="none"
        className="w-4 h-4 text-[#C45A3B]"
        aria-hidden="true"
      >
        {/* Fountain pen nib - clean and recognizable */}
        <path
          d="M15.5 5.5L18.5 8.5M6 21L3 18L14.5 6.5C15.328 5.672 16.672 5.672 17.5 6.5C18.328 7.328 18.328 8.672 17.5 9.5L6 21ZM6 21H3V18"
          stroke="currentColor"
          strokeWidth="1.5"
          strokeLinecap="round"
          strokeLinejoin="round"
        />
      </svg>
    </div>
  )
}
