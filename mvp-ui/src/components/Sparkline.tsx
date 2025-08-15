type Props = { data: number[]; width?: number; height?: number; strokeWidth?: number }
export default function Sparkline({ data, width=120, height=40, strokeWidth=2 }: Props) {
  const min = Math.min(...data), max = Math.max(...data)
  const points = data.map((d,i) => {
    const x = (i / Math.max(1, data.length-1)) * width
    const y = height - ((d - min) / (max - min || 1)) * height
    return `${x},${y}`
  }).join(' ')
  return (
    <svg width={width} height={height} viewBox={`0 0 ${width} ${height}`}>
      <polyline fill="none" stroke="currentColor" strokeWidth={strokeWidth} points={points} />
    </svg>
  )
}
