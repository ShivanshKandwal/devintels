export default function TechPill({ name, selected = false, onClick, className = '' }) {
  return (
    <button
      onClick={onClick}
      className={`
        inline-flex items-center px-4 py-2 rounded-full text-sm font-semibold
        transition-all duration-200 cursor-pointer select-none
        ${
          selected
            ? 'bg-purple-accent text-white shadow-md shadow-purple-accent/25'
            : 'bg-transparent text-text-secondary border border-dark-border hover:border-purple-accent/50 hover:text-purple-light'
        }
        ${className}
      `}
    >
      {name}
    </button>
  )
}
