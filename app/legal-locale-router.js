/* BibleMind mobile app legal language router.
   Website-only notices are intentionally outside /app/ and are NEVER routed.
   Never silently display English as if it were a complete translation. */
(function () {
  'use strict';
  const valid = [
    'en','hu','es','pt','ro','de','it','pl','fr','nl',
    'zh-hans','zh-hant','vi','hi','th','uk','ru','el'
  ];
  const available = new Set(['en', 'ro']);
  const names = {
    'en':'English', 'hu':'Magyar', 'es':'Español', 'pt':'Português',
    'ro':'Română', 'de':'Deutsch', 'it':'Italiano', 'pl':'Polski',
    'fr':'Français', 'nl':'Nederlands', 'zh-hans':'简体中文',
    'zh-hant':'繁體中文', 'vi':'Tiếng Việt', 'hi':'हिन्दी',
    'th':'ไทย', 'uk':'Українська', 'ru':'Русский', 'el':'Ελληνικά'
  };
  // A fallback notice is localized even though the complete document is not.
  const fallback = {
    'hu':'A teljes jogi dokumentum magyar fordítása még ellenőrzés alatt áll. Jelenleg az angol teljes szöveg olvasható.',
    'es':'La traducción completa de este documento jurídico al español aún está pendiente de revisión. Por ahora se muestra el texto completo en inglés.',
    'pt':'A tradução integral deste documento jurídico para português ainda aguarda revisão. Por enquanto, é apresentada a versão completa em inglês.',
    'de':'Die vollständige deutsche Übersetzung dieses Rechtstextes wird noch geprüft. Bis dahin wird die vollständige englische Fassung angezeigt.',
    'it':'La traduzione italiana completa di questo documento legale è ancora in fase di revisione. Per ora viene mostrata la versione integrale inglese.',
    'pl':'Pełne polskie tłumaczenie tego dokumentu prawnego oczekuje na weryfikację. Obecnie wyświetlana jest pełna wersja angielska.',
    'fr':'La traduction française intégrale de ce document juridique est encore en cours de vérification. Le texte anglais complet est affiché pour le moment.',
    'nl':'De volledige Nederlandse vertaling van dit juridische document moet nog worden gecontroleerd. Voorlopig wordt de volledige Engelse tekst weergegeven.',
    'zh-hans':'本法律文件的完整简体中文译文尚待审核。目前显示完整英文版本。',
    'zh-hant':'本法律文件的完整繁體中文譯文尚待審核。目前顯示完整英文版本。',
    'vi':'Bản dịch đầy đủ của tài liệu pháp lý này sang tiếng Việt vẫn đang chờ rà soát. Hiện tại tài liệu được hiển thị đầy đủ bằng tiếng Anh.',
    'hi':'इस कानूनी दस्तावेज़ के पूर्ण हिन्दी अनुवाद की समीक्षा अभी शेष है। फिलहाल पूरा अंग्रेज़ी पाठ दिखाया गया है।',
    'th':'คำแปลภาษาไทยฉบับสมบูรณ์ของเอกสารกฎหมายนี้ยังอยู่ระหว่างการตรวจสอบ ขณะนี้แสดงเนื้อหาฉบับภาษาอังกฤษเต็มรูปแบบ',
    'uk':'Повний український переклад цього юридичного документа ще проходить перевірку. Наразі відображається повний текст англійською мовою.',
    'ru':'Полный перевод этого юридического документа на русский язык ещё проходит проверку. Пока отображается полный текст на английском языке.',
    'el':'Η πλήρης ελληνική μετάφραση αυτού του νομικού εγγράφου βρίσκεται ακόμη υπό έλεγχο. Προς το παρόν εμφανίζεται ολόκληρο το αγγλικό κείμενο.'
  };
  function normalize(raw) {
    const s = String(raw || '').trim().toLowerCase().replace(/_/g, '-');
    if (s === 'zh' || s === 'zh-cn' || s === 'zh-sg') return 'zh-hans';
    if (s === 'zh-tw' || s === 'zh-hk' || s === 'zh-mo') return 'zh-hant';
    if (s.startsWith('zh-hant')) return 'zh-hant';
    if (s.startsWith('zh-hans')) return 'zh-hans';
    const code = s.split('-')[0];
    return valid.includes(s) ? s : (valid.includes(code) ? code : 'en');
  }
  const filename = location.pathname.split('/').pop();
  if (!['privacy.html','terms.html','copyright.html','data-deletion.html'].includes(filename)) return;
  // Only top-level /app/ English documents get language routing.
  if (!/^\/app\/(privacy|terms|copyright|data-deletion)\.html$/.test(location.pathname)) return;
  const search = new URLSearchParams(location.search);
  const requested = search.has('lang')
    ? search.get('lang')
    : (navigator.languages && navigator.languages[0]) || navigator.language || 'en';
  const language = normalize(requested);
  if (language === 'ro') {
    // Prevent redirect loops: translated pages live in /app/ro/.
    location.replace('/app/ro/' + filename + location.hash);
    return;
  }
  const siblingNames = {
    'privacy.html':'Confidențialitate', 'terms.html':'Termeni de utilizare',
    'copyright.html':'Drepturi de autor', 'data-deletion.html':'Ștergerea datelor'
  };
  document.addEventListener('DOMContentLoaded', function () {
    const article = document.querySelector('main.legal article.paper');
    if (!article) return;
    const languageBar = document.createElement('div');
    languageBar.style.cssText = 'margin:1rem 0;padding:.85rem 1rem;border-radius:12px;background:#f3f0e9;font-size:.95rem;line-height:1.6;';
    const englishLink = document.createElement('a');
    englishLink.href = '/app/' + filename + '?lang=en';
    englishLink.textContent = 'English';
    const romanianLink = document.createElement('a');
    romanianLink.href = '/app/ro/' + filename;
    romanianLink.textContent = 'Română';
    languageBar.append(englishLink, document.createTextNode(' · '), romanianLink);
    if (language !== 'en' && !available.has(language)) {
      const message = document.createElement('p');
      message.setAttribute('lang', language === 'zh-hans' || language === 'zh-hant' ? 'zh' : language);
      message.textContent = fallback[language] || 'The complete legal document is currently available in English.';
      message.style.marginBottom = '.45rem';
      languageBar.prepend(message);
      document.documentElement.lang = 'en'; // Actual rendered document remains English.
    }
    const eyebrow = article.querySelector('.eyebrow');
    if (eyebrow) eyebrow.insertAdjacentElement('afterend', languageBar);
    // Carry the requested language into other mobile-app legal links, not website-only links.
    document.querySelectorAll('a[href^="/app/"]').forEach(function (a) {
      if (language === 'en') return;
      const href = a.getAttribute('href') || '';
      if (!/^\/app\/(privacy|terms|copyright|data-deletion)\.html$/.test(href)) return;
      a.setAttribute('href', href + '?lang=' + encodeURIComponent(language));
    });
  });
})();
