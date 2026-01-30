import { defineConfig } from 'vitepress';
import mermaid from 'mermaid';  // Importa mermaid para inicialización
import { withMermaid } from 'vitepress-plugin-mermaid';  // Usa la helper

export default withMermaid(
  defineConfig({
    title: "Maya | Signer",
    description: "Servicio de firma electrónica para Maya (Odoo)",
    lang: 'es-ES',

    // Para GitHub Pages
    base: '/maya-signer/',
    srcDir: './src',

    ignoreDeadLinks: true,

    mermaid: {
      theme: 'dark'
    },

    themeConfig: {
      logo: '/logo.png',
      
      nav: [
        { text: 'Inicio', link: '/' },
      ],
    }
  })
)