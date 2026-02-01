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
      { text: 'Guía de Usuario', link: '/user/getting-started' },
      { text: 'Guía de Desarrollo', link: '/dev/overview' },
      { 
        text: 'v0.3.0',
        items: [
          { text: 'Changelog', link: '/changelog' },
          { text: 'Releases', link: 'https://github.com/Maya-AQSS/maya-signer/releases' }
        ]
      }
    ],

      sidebar: {
        '/user/': [
          {
            text: 'Guía de Usuario',
            items: [
              { text: 'Comenzar', link: '/user/getting-started' },
              { text: 'Instalación', link: '/user/installation' },
              { text: 'Firmar Documentos', link: '/user/signing' },
              { text: 'Troubleshooting', link: '/user/troubleshooting' }
            ]
          },
          {
            text: 'Plataformas',
            items: [
              { text: 'Linux', link: '/user/platforms/linux' },
              { text: 'Windows', link: '/user/platforms/windows' },
              { text: 'macOS', link: '/user/platforms/macos' }
            ]
          },
          {
            text: 'Certificados',
            items: [
              { text: 'Certificados .p12/.pfx', link: '/user/certificates/p12' },
              { text: 'DNIe', link: '/user/certificates/dnie' }
            ]
          }
        ],       
      },

      socialLinks: [
        { icon: 'github', link: 'https://github.com/Maya-AQSS/maya-signer' }
      ],

      footer: {
        message: 'Publicado bajo Licencia GPL 3.0',
        copyright: 'Copyright © 2026 Alfredo Oltra'
      },
      search: {
        provider: 'local'
      },

      editLink: {
        pattern: 'https://github.com/Maya-AQSS/maya-signer/edit/main/docs/:path',
        text: 'Editar esta página en GitHub'
      },

      lastUpdated: {
        text: 'Última actualización',
        formatOptions: {
          dateStyle: 'short',
          timeStyle: 'short'
        }
      }
    }
  })
)