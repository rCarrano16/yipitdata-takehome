/// <reference types="vite/client" />

// Declares the one custom environment variable the app reads, so
// import.meta.env.VITE_API_BASE_URL is typed instead of `any`.
interface ImportMetaEnv {
  readonly VITE_API_BASE_URL?: string
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}
