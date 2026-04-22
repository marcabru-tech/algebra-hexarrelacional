/**
 * src/lib/i18n.ts — Internationalisation for the Hexarelational Significance Platform.
 *
 * Supports: pt_BR, en, zh, ja, ar (RTL).
 */

export type Lang = 'pt_BR' | 'en' | 'zh' | 'ja' | 'ar';

const RTL_LANGS: Lang[] = ['ar'];

const SUPPORTED_LANGS: Lang[] = ['en', 'pt_BR', 'zh', 'ja', 'ar'];

const DEFAULT_LANG: Lang = 'en';

// ---------------------------------------------------------------------------
// Translation tables
// ---------------------------------------------------------------------------

const translations: Record<Lang, Record<string, string>> = {
  en: {
    'app.name': 'Hexarelational Significance Algebra',
    'nav.dashboard': 'Dashboard',
    'nav.relations': 'Relations',
    'nav.operators': 'Operators',
    'nav.settings': 'Settings',
    'plan.runs_per_day': '{count} runs per day',
    'error.run.timeout': 'Timeout after {seconds} seconds',
    'error.run.input_too_large': 'Input too large ({kb} KB)',
  },
  pt_BR: {
    'app.name': 'Álgebra de Significância Hexarrelacional',
    'nav.dashboard': 'Painel',
    'nav.relations': 'Relações',
    'nav.operators': 'Operadores',
    'nav.settings': 'Configurações',
    'plan.runs_per_day': '{count} execuções por dia',
    'error.run.timeout': 'Tempo limite após {seconds} segundos',
    'error.run.input_too_large': 'Entrada muito grande ({kb} KB)',
  },
  zh: {
    'app.name': '六元关系显著性代数',
    'nav.dashboard': '仪表盘',
    'nav.relations': '关系',
    'nav.operators': '运算符',
    'nav.settings': '设置',
    'plan.runs_per_day': '每天 {count} 次运行',
    'error.run.timeout': '{seconds} 秒后超时',
    'error.run.input_too_large': '输入过大（{kb} KB）',
  },
  ja: {
    'app.name': '六元関係有意性代数',
    'nav.dashboard': 'ダッシュボード',
    'nav.relations': '関係',
    'nav.operators': '演算子',
    'nav.settings': '設定',
    'plan.runs_per_day': '1日あたり {count} 回実行',
    'error.run.timeout': '{seconds} 秒後にタイムアウト',
    'error.run.input_too_large': '入力が大きすぎます（{kb} KB）',
  },
  ar: {
    'app.name': 'جبر الأهمية السداسية العلائقية',
    'nav.dashboard': 'لوحة التحكم',
    'nav.relations': 'العلاقات',
    'nav.operators': 'المشغلون',
    'nav.settings': 'الإعدادات',
    'plan.runs_per_day': '{count} تشغيل في اليوم',
    'error.run.timeout': 'انتهت المهلة بعد {seconds} ثانية',
    'error.run.input_too_large': 'الإدخال كبير جداً ({kb} كيلوبايت)',
  },
};

// ---------------------------------------------------------------------------
// Public API
// ---------------------------------------------------------------------------

/**
 * Translate a key to the given language with parameter interpolation.
 *
 * @param key - Translation key, e.g. "nav.dashboard".
 * @param lang - Target language code. Defaults to 'en'.
 * @param params - Interpolation parameters, e.g. { count: 10 }.
 * @returns Translated string with interpolated parameters.
 *          Falls back to English, then to the key itself.
 */
export function t(
  key: string,
  lang: Lang = DEFAULT_LANG,
  params?: Record<string, string | number>,
): string {
  let text = translations[lang]?.[key];
  if (text === undefined && lang !== DEFAULT_LANG) {
    text = translations[DEFAULT_LANG]?.[key];
  }
  if (text === undefined) {
    return key;
  }
  if (params) {
    text = text.replace(/\{(\w+)\}/g, (_, name) => {
      const val = params[name];
      return val !== undefined ? String(val) : `{${name}}`;
    });
  }
  return text;
}

/**
 * Check if the language uses right-to-left layout.
 */
export function isRtl(lang: Lang): boolean {
  return (RTL_LANGS as string[]).includes(lang);
}

/**
 * Return list of supported language codes.
 */
export function getSupportedLangs(): Lang[] {
  return [...SUPPORTED_LANGS];
}

/**
 * Get the display name of a language in a given language.
 */
export function getLangLabel(lang: Lang, displayLang: Lang = 'en'): string {
  const labels: Record<Lang, Record<Lang, string>> = {
    en: {
      en: 'English',
      pt_BR: 'Inglês',
      zh: '英语',
      ja: '英語',
      ar: 'الإنجليزية',
    },
    pt_BR: {
      en: 'Português (BR)',
      pt_BR: 'Português (BR)',
      zh: '葡萄牙语',
      ja: 'ポルトガル語',
      ar: 'البرتغالية',
    },
    zh: {
      en: 'Chinese (Simplified)',
      pt_BR: 'Chinês',
      zh: '简体中文',
      ja: '簡体字中国語',
      ar: 'الصينية',
    },
    ja: {
      en: 'Japanese',
      pt_BR: 'Japonês',
      zh: '日语',
      ja: '日本語',
      ar: 'اليابانية',
    },
    ar: {
      en: 'Arabic',
      pt_BR: 'Árabe',
      zh: '阿拉伯语',
      ja: 'アラビア語',
      ar: 'العربية',
    },
  };
  return labels[lang]?.[displayLang] ?? lang;
}
