import tokens from '../../design-tokens.json'

export default function Heading({ level = 1, children }: { level?: 1 | 2 | 3; children: React.ReactNode }) {
  const Tag: any = `h${level}`
  const sizes: Record<number, string> = {
    1: tokens.typography.h1,
    2: tokens.typography.h2,
    3: tokens.typography.h3,
  }
  const style = { fontSize: sizes[level] }
  const classes = 'font-semibold text-white leading-tight'
  return <Tag style={style as any} className={classes}>{children}</Tag>
}
