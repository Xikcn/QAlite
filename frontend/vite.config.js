import { fileURLToPath, URL } from 'node:url'

import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
// 注释掉Vue DevTools插件
// import vueDevTools from 'vite-plugin-vue-devtools'

// https://vite.dev/config/
export default defineConfig({
  plugins: [
    vue(),
    // 禁用Vue DevTools插件
    // vueDevTools(),
  ],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url))
    },
  },
  // 添加兼容老版本Node.js的配置
  esbuild: {
    // 将目标设置为ES2015，避免使用较新的语法特性
    target: 'es2015',
    // 禁用现代JavaScript语法转换
    supported: {
      'nullish-coalescing': false, // 禁用??运算符
      'optional-chaining': false,  // 禁用?.运算符
      'logical-assignment': false, // 禁用||=、&&=、??=运算符
    },
  },
  // 强制指定Node.js兼容性
  build: {
    target: 'es2015',
  }
})
