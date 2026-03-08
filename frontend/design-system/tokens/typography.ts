export const typographyTokens = {
  family: {
    display: "'Space Grotesk', 'Segoe UI', sans-serif",
    body: "'Plus Jakarta Sans', 'Segoe UI', sans-serif",
    mono: "'JetBrains Mono', monospace"
  },
  size: {
    hero: "clamp(2.6rem, 6vw, 5.5rem)",
    title: "clamp(1.8rem, 3vw, 3rem)",
    section: "clamp(1.3rem, 2vw, 1.8rem)",
    narrative: "1.1rem",
    body: "1rem",
    caption: "0.84rem",
    quiz: "1.15rem"
  },
  weight: {
    regular: 400,
    medium: 500,
    semibold: 600,
    bold: 700
  },
  lineHeight: {
    compact: 1.15,
    normal: 1.5,
    relaxed: 1.75
  }
} as const;
