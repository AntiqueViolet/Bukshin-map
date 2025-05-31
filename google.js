const puppeteer = require('puppeteer');
const XLSX = require('xlsx');
const fs = require('fs').promises;

async function parseGoogleMaps(searchQuery, maxResults = 30) {
  const browser = await puppeteer.launch({ headless: true });
  const page = await browser.newPage();
  
  // Включим логирование для отладки
  page.on('console', msg => console.log('PAGE LOG:', msg.text()));
  
  // Устанавливаем User-Agent
  await page.setUserAgent('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36');
  
  console.log(`Перехожу по URL: https://www.google.com/maps/search/${encodeURIComponent(searchQuery)}`);
  await page.goto(`https://www.google.com/maps/search/${encodeURIComponent(searchQuery)}`, {
    waitUntil: 'networkidle2',
    timeout: 120000
  });

  try {
    // Ждем появления контейнера с результатами
    console.log('Ожидаю появления результатов...');
    await page.waitForSelector('[role="feed"], .Nv2PK, .section-result', { timeout: 30000 });
  } catch (e) {
    console.error('Не удалось найти контейнер результатов:', e);
    const content = await page.content();
    await fs.writeFile('debug_error.html', content);
    console.error('Сохранен файл debug_error.html для анализа');
  }

  // Улучшенный скроллинг
  let resultsCount = 0;
  let lastCount = 0;
  let retries = 0;
  const maxRetries = 5;
  let scrollAttempts = 0;
  const maxScrollAttempts = 50;

  // Основной контейнер для прокрутки
  const scrollContainer = await page.$('[role="feed"]') || await page.$('.m6QErb.DxBCM');
  
  console.log('Начинаю прокрутку...');
  while (resultsCount < maxResults && retries < maxRetries && scrollAttempts < maxScrollAttempts) {
    scrollAttempts++;
    
    // Прокручиваем контейнер или страницу
    if (scrollContainer) {
      await scrollContainer.evaluate(el => {
        // Прокручиваем на 80% высоты контейнера
        el.scrollTop += el.clientHeight * 0.8;
      });
    } else {
      await page.evaluate(() => {
        window.scrollBy(0, window.innerHeight * 0.8);
      });
    }

    // Ждем загрузки (динамическое ожидание)
    await new Promise(resolve => setTimeout(resolve, 2000));
    
    // Ожидаем появления новых элементов или спиннера
    try {
      await Promise.race([
        page.waitForSelector('[role="article"]:not(.section-result):last-child', { timeout: 3000 }),
        page.waitForSelector('.Nv2PK:last-child', { timeout: 3000 }),
        page.waitForSelector('.section-result:last-child', { timeout: 3000 })
      ]);
    } catch (e) {
      console.log('Новые элементы не появились');
    }

    // Считаем текущее количество результатов
    const currentCount = await page.$$eval(
      '[role="article"], .Nv2PK, .section-result', 
      elements => elements.length
    );
    
    console.log(`Попытка ${scrollAttempts}: Найдено ${currentCount} результатов`);
    
    // Проверяем, увеличилось ли количество
    if (currentCount === lastCount) {
      retries++;
      console.log(`Количество не изменилось, попытка ${retries}/${maxRetries}`);
    } else {
      retries = 0;
      lastCount = currentCount;
    }
    
    resultsCount = currentCount;
    
    // Проверяем наличие кнопки "Больше результатов"
    try {
      const moreButton = await page.$('button[aria-label^="Больше результатов"], button[aria-label^="More results"]');
      if (moreButton) {
        console.log('Найдена кнопка "Больше результатов", нажимаю...');
        await moreButton.evaluate(b => b.click());
        await new Promise(resolve => setTimeout(resolve, 4000));
        retries = 0;  // Сброс после нажатия кнопки
      }
    } catch (e) {
      console.error('Ошибка при клике на кнопку:', e);
    }
  }

  console.log(`Прокрутка завершена. Всего найдено ${resultsCount} результатов`);

const data = await page.evaluate(() => {
  const items = [];
  const cards = document.querySelectorAll('[role="article"], .Nv2PK, .section-result');
  
  cards.forEach((card) => {
    // Название компании
    const nameElement = card.querySelector('.fontHeadlineSmall, .qBF1Pd, .section-result-title');
    const name = nameElement ? nameElement.textContent.trim() : '';
    
    // Адрес - точный селектор
    let address = '';
    const addressSpan = card.querySelector('.W4Efsd > div > span:last-child > span:last-child');
    
    if (addressSpan) {
      address = addressSpan.textContent.trim();
    }

    if (name && address) {
      items.push({ name, address });
    }
  });
  
  return items;
});

  await browser.close();
  return data.slice(0, maxResults);
}

// Функция сохранения в XLSX
function saveToXLSX(data, filename) {
  const ws = XLSX.utils.json_to_sheet(data);
  const wb = XLSX.utils.book_new();
  XLSX.utils.book_append_sheet(wb, ws, 'Results');
  XLSX.writeFile(wb, filename);
}

(async () => {
  try {
    const searchQuery = 'пункт техосмотра Новосибирск';
    console.log(`Начинаю поиск: "${searchQuery}"`);
    const results = await parseGoogleMaps(searchQuery);
    
    console.log(`Получено ${results.length} результатов`);
    
    if (results.length > 0) {
      saveToXLSX(results, 'technical_inspection_points.xlsx');
      console.log(`Данные сохранены в technical_inspection_points.xlsx`);
      
      // Выводим первые 3 результата для проверки
      console.log('Примеры результатов:');
      results.slice(0, 3).forEach((item, i) => {
        console.log(`${i + 1}. ${item.name} - ${item.address}`);
      });
    } else {
      console.log('Данные не найдены');
    }
  } catch (error) {
    console.error('Критическая ошибка:', error);
  }
})();