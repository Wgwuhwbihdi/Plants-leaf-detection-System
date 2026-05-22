// Internationalization (i18n) utility
class I18n {
  constructor() {
    this.currentLocale = localStorage.getItem('phytoLocale') || this.getCookieLocale() || 'en';
    this.translations = {};
    this.supportedLocales = ['en', 'es', 'fr', 'hi', 'mr'];
    this.init();
  }

  getCookieLocale() {
    const cookie = document.cookie
      .split('; ')
      .find(row => row.startsWith('lang='));
    return cookie ? decodeURIComponent(cookie.split('=')[1]) : null;
  }

  async init() {
    await this.loadLocale(this.currentLocale);
    this.applyTranslations();
    document.documentElement.lang = this.currentLocale;
  }

  async loadLocale(locale) {
    if (!this.supportedLocales.includes(locale)) {
      locale = 'en';
    }
    try {
      const response = await fetch(`/static/locales/${locale}.json`);
      this.translations = await response.json();
      this.currentLocale = locale;
      localStorage.setItem('phytoLocale', locale);
      document.documentElement.lang = locale;
    } catch (error) {
      console.error(`Failed to load locale ${locale}:`, error);
      if (locale !== 'en') {
        await this.loadLocale('en');
      }
    }
  }

  t(key, defaultValue = key) {
    return this.getNestedValue(this.translations, key) || defaultValue;
  }

  getNestedValue(obj, key) {
    const keys = key.split('.');
    let value = obj;
    for (const k of keys) {
      if (value && typeof value === 'object' && k in value) {
        value = value[k];
      } else {
        return null;
      }
    }
    return value;
  }

  async setLocale(locale) {
    await this.loadLocale(locale);
    this.applyTranslations();
  }

  getAvailableLocales() {
    return this.supportedLocales;
  }

  getCurrentLocale() {
    return this.currentLocale;
  }

  applyTranslations() {
    // Apply to data-i18n attributes
    document.querySelectorAll('[data-i18n]').forEach(element => {
      const key = element.getAttribute('data-i18n');
      const text = this.t(key);
      if (element.tagName === 'INPUT' || element.tagName === 'TEXTAREA') {
        element.placeholder = text;
      } else {
        element.textContent = text;
      }
    });

    // Apply to data-i18n-title attributes
    document.querySelectorAll('[data-i18n-title]').forEach(element => {
      const key = element.getAttribute('data-i18n-title');
      element.title = this.t(key);
    });

    // Trigger custom event for components that need re-rendering
    window.dispatchEvent(new Event('i18n-changed'));
  }
}

// Initialize i18n globally
const i18n = new I18n();
