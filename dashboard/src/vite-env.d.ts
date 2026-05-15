/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_AEGIS_API_URL?: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
