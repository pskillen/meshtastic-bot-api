/** @type {import('tailwindcss').Config} */
module.exports = {
    content: [
        "./MeshtasticBotManager/templates/**/*.html.j2",
        "./MessageViewer/templates/**/*.html.j2",
    ],
    theme: {
        extend: {},
    },
    plugins: [require("daisyui")],  // If using DaisyUI
};
