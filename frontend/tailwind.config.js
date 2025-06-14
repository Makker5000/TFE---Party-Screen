// /** @type {import('tailwindcss').Config} */
// export default {
//   content: ["./src/**/*.{html,js,svelte,ts}"],

//   theme: {
//     extend: {}
//   },

//   plugins: [require("@tailwindcss/typography")]
// };
// ------------------------------
import daisyui from 'daisyui'

/** @type {import('tailwindcss').Config} */
export default {
  content: ['./src/**/*.{html,js,svelte,ts}'],
  theme: {
    extend: {
      keyframes: {
        slideIn: {
          '0%': { transform: 'translateX(-100%)', opacity: '0' },
          '100%': { transform: 'translateX(0)', opacity: '1' },
        },
      },
      animation: {
        'slide-in': 'slideIn 0.8s ease-out',
      },
    },
  },
  plugins: [daisyui]
}