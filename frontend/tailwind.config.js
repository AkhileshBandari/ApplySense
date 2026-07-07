/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        darkBg: '#090a0f',
        cardBg: '#121420',
        cardBorder: '#1c1f32',
        accentTeal: '#00f2fe',
        accentPurple: '#a100ff',
        primaryText: '#e2e8f0',
        secondaryText: '#94a3b8',
      },
      backgroundImage: {
        'gradient-cyan-purple': 'linear-gradient(135deg, #00f2fe 0%, #4facfe 50%, #a100ff 100%)',
        'dark-radial': 'radial-gradient(circle at top, #1e293b 0%, #0f172a 100%)',
      },
      boxShadow: {
        'neon-teal': '0 0 15px rgba(0, 242, 254, 0.35)',
        'neon-purple': '0 0 15px rgba(161, 0, 255, 0.35)',
        'glass': '0 8px 32px 0 rgba(0, 0, 0, 0.37)',
      }
    },
  },
  plugins: [],
}
