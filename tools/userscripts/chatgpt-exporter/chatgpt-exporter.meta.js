// ==UserScript==
// @name         ChatGPT Exporter for Agents
// @namespace    https://github.com/wyattowalsh/agents
// @version      1.0.0
// @description  Privacy-first, rate-limit-aware ChatGPT exports for people and downstream agents: Markdown, JSON, JSONL, HTML, CSV, text, gzip, clipboard, and print/PDF.
// @author       Wyatt Walsh
// @license      MIT
// @match        https://chatgpt.com/*
// @match        https://chat.openai.com/*
// @run-at       document-idle
// @inject-into  page
// @noframes
// @grant        GM_getValue
// @grant        GM_setValue
// @grant        GM_setClipboard
// @grant        GM_registerMenuCommand
// @grant        CAT_userConfig
// @grant        unsafeWindow
// @grant        window.onurlchange
// @downloadURL  https://chatgpt-export-local.vercel.app/chatgpt-exporter.user.js
// @updateURL    https://chatgpt-export-local.vercel.app/chatgpt-exporter.meta.js
// @homepageURL  https://github.com/wyattowalsh/agents/tree/main/tools/userscripts/chatgpt-exporter
// @supportURL   https://github.com/wyattowalsh/agents/issues
// @source       https://github.com/wyattowalsh/agents/tree/main/tools/userscripts/chatgpt-exporter
// ==/UserScript==
