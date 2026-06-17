import { createI18n } from 'vue-i18n'

const messages = {
  en: {
    brand: {
      name: 'FACTORY',
      accent: 'COPILOT',
      tagline: 'Intelligent assistant for factory operations',
    },
    login: {
      username: 'Username',
      password: 'Password',
      signIn: 'Sign In',
      errorEmpty: 'Username and password are required.',
      errorFail: 'Login failed. Check your credentials.'
    },
    inventory: {
      title: 'Factory Inventory (Odoo Sync)',
      syncBtn: 'Sync Odoo ERP',
      searchPlaceholder: 'Search by item name or SKU...',
      thItem: 'Item Name',
      thSku: 'SKU / Part Number',
      thQty: 'Quantity',
      thLocation: 'Location',
      thStatus: 'Status',
      statusInStock: 'In Stock',
      statusLowStock: 'Low Stock',
      statusOutOfStock: 'Out of Stock'
    },
    workflow: {
      demoBadge: 'MVP Demo',
      welcome: 'Hello! I am ready to automate your factory workflows. Paste your rule below.',
      placeholder: 'Paste your automation rule here...',
      send: 'Send',
      understood: '<strong>Understood.</strong> I am configuring the automation and routing the alert to your email. Generating logic sequence...',
      complete: 'Workflow complete! You can drag the nodes or use your mouse wheel to zoom in and out of the canvas.'
    },
    docs: {
      title: 'Knowledge Base',
      dragZone: 'Drag & Drop PDF manual or click to browse',
      onlyPdf: 'Supports PDF manuals only',
      statusProcessing: 'Processing Chunks...',
      statusCompleted: 'Ready for RAG',
      statusFailed: 'Ingestion Failed',
      empty: 'No technical reference manuals uploaded yet.',
      chunks: 'chunks'
    },
    chat: {
      placeholder: 'Ask about inventory, safety, or Odoo...',
      send: 'Send',
      sources: 'Sources',
      clear: 'Clear Chat',
      preview: 'Previewing Document'
    },
    logs: {
      title: 'AI & Automation Logs',
      refresh: 'Refresh Logs',
      search: 'Search prompts...',
      thTime: 'Timestamp',
      thUser: 'User / Session',
      thPrompt: 'User Prompt',
      thTool: 'Tool Used',
      thLatency: 'Latency',
      toolDocs: 'Search Docs',
      toolOdoo: 'Query Odoo',
      toolNone: 'Direct Chat',
      empty: 'No logs found.'
    },
    nav: {
      chat: 'Chat',
      docs: 'Documents',
      inventory: 'Inventory',
      workflow: 'Workflow Automation',
      logs: 'System Logs',
      admin: 'Admin Panel',
      logout: 'Logout'
    }
  },
  ar: {
    brand: {
      name: 'فاكتوري',
      accent: 'كو بايلوت ',
      tagline: 'مساعد ذكي لعمليات المصنع',
    },
    chat: {
      placeholder: 'اسأل عن المخزون، السلامة، أو أودو...',
      send: 'إرسال',
      sources: 'المصادر',
      clear: 'مسح المحادثة',
      preview: 'معاينة المستند'
    },
    workflow: {
      demoBadge: 'نسخة تجريبية',
      welcome: 'مرحباً! أنا مستعد لأتمتة سير عمل المصنع. ألصق قاعدتك بالأسفل.',
      placeholder: 'ألصق قاعدة الأتمتة هنا...',
      send: 'إرسال',
      understood: '<strong>مفهوم.</strong> أقوم بتكوين الأتمتة وتوجيه التنبيه إلى بريدك الإلكتروني. جاري إنشاء التسلسل المنطقي...',
      complete: 'اكتمل سير العمل! يمكنك سحب العقد أو استخدام عجلة الماوس للتكبير والتصغير في لوحة العمل.'
    },
    logs: {
      title: 'سجلات الذكاء الاصطناعي والأتمتة',
      refresh: 'تحديث السجلات',
      search: 'البحث في المطالبات...',
      thTime: 'الوقت',
      thUser: 'المستخدم / الجلسة',
      thPrompt: 'المطالبة',
      thTool: 'الأداة المستخدمة',
      thLatency: 'الاستجابة',
      toolDocs: 'البحث في المستندات',
      toolOdoo: 'استعلام أودو',
      toolNone: 'محادثة مباشرة',
      empty: 'لم يتم العثور على سجلات.'
    },
    inventory: {
      title: 'مخزون المصنع (مزامنة أودو)',
      syncBtn: 'مزامنة نظام أودو',
      searchPlaceholder: 'البحث حسب اسم الصنف أو رمز SKU...',
      thItem: 'اسم الصنف',
      thSku: 'رقم القطعة / SKU',
      thQty: 'الكمية',
      thLocation: 'الموقع',
      thStatus: 'الحالة',
      statusInStock: 'متوفر',
      statusLowStock: 'مخزون منخفض',
      statusOutOfStock: 'غير متوفر'
    },
    docs: {
      title: 'قاعدة المعرفة',
      dragZone: 'اسحب وأسقط دليل الـ PDF أو انقر للتصفح',
      onlyPdf: 'يدعم كتيبات ومستندات PDF فقط',
      statusProcessing: 'جاري المعالجة والتقطيع...',
      statusCompleted: 'جاهز للاسترجاع (RAG)',
      statusFailed: 'فشل التحليل',
      empty: 'لم يتم رفع أي أدلة مرجعية فنية بعد.',
      chunks: 'أجزاء نصوص'
    },
    login: {
      username: 'اسم المستخدم',
      password: 'كلمة المرور',
      signIn: 'تسجيل الدخول',
      errorEmpty: 'اسم المستخدم وكلمة المرور مطلوبان.',
      errorFail: 'فشل تسجيل الدخول. تحقق من بياناتك.'
    },
    nav: {
      chat: 'المحادثة',
      docs: 'المستندات',
      inventory: 'المخزون',
      workflow: 'أتمتة سير العمل',
      logs: 'سجلات النظام',
      admin: 'لوحة التحكم',
      logout: 'تسجيل الخروج'
    }
  }
}

const i18n = createI18n({
  legacy: false, // Essential for Vue 3 Composition API setup
  locale: 'en',  // Default language
  fallbackLocale: 'en',
  messages,
})

export default i18n