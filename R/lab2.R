# Установка и загрузка необходимых пакетов
if (!require("pacman")) install.packages("pacman")
pacman::p_load(
  rvest,      # для веб-скрапинга
  xml2,       # работа с XML/HTML
  httr,       # HTTP-запросы
  dplyr,      # манипуляции с данными
  stringr,    # работа со строками
  tm,         # текстовая аналитика
  wordcloud,  # облако слов
  RColorBrewer # цветовые палитры
)

# Функция для получения ссылок из результатов поиска
get_search_results <- function(search_url, keyword) {
  tryCatch({
    # Выполняем GET-запрос к поисковой выдаче
    search_page <- httr::GET(search_url)
    
    # Проверяем успешность запроса
    if (httr::status_code(search_page) != 200) {
      stop("Ошибка при загрузке страницы поиска")
    }
    
    # Парсим HTML
    html_content <- read_html(search_page$content)
    
    # Извлекаем все ссылки
    all_links <- html_content %>%
      html_nodes("a") %>%
      html_attr("href")
    
    # Фильтруем только ссылки на конкретные статьи
    article_links <- all_links[grepl("/news/|/article/", all_links) & 
                                 !grepl("/category/|/tag/|/author/", all_links)]
    
    # Убираем дубликаты
    article_links <- unique(article_links)
    
    # Преобразуем относительные ссылки в абсолютные
    base_domain <- "https://gubdaily.ru"
    article_links <- ifelse(grepl("^https?://", article_links), 
                            article_links, 
                            paste0(base_domain, article_links))
    
    # Вывод для отладки
    cat("Всего найдено ссылок на странице:", length(all_links), "\n")
    cat("После фильтрации осталось статей:", length(article_links), "\n")
    
    if (length(article_links) > 0) {
      cat("Первые 5 найденных статей:\n")
      for (i in 1:min(5, length(article_links))) {
        cat(i, ":", article_links[i], "\n")
      }
    }
    
    return(article_links)
    
  }, error = function(e) {
    cat("Ошибка при получении результатов поиска:", e$message, "\n")
    return(character(0))
  })
}

# Функция для извлечения чистого текста статьи
extract_article_text <- function(article_url) {
  tryCatch({
    # Загружаем страницу статьи
    article_page <- httr::GET(article_url, timeout(10))
    
    if (httr::status_code(article_page) != 200) {
      cat("Ошибка HTTP:", httr::status_code(article_page), "для URL:", article_url, "\n")
      return("")
    }
    
    html_content <- read_html(article_page$content)
    
    # Основной селектор для GUBDAILY.RU
    # Извлекаем текст из основного контентного блока
    main_content <- html_content %>% html_nodes("#content-main")
    
    if (length(main_content) > 0) {
      # Удаляем ненужные элементы из основного контента
      main_content %>% 
        html_nodes("script, style, .social-sharing-top, .gub-ad-desc, .gub-ad-mob, .gub-ad-gray, .ai-viewport-3, .code-block") %>% 
        xml_remove()
      
      # Извлекаем все параграфы и цитаты
      paragraphs <- main_content %>% html_nodes("p, blockquote p") %>% html_text(trim = TRUE)
      
      # Фильтруем слишком короткие параграфы
      paragraphs <- paragraphs[nchar(paragraphs) > 30]
      article_text <- paste(paragraphs, collapse = " ")
      
    } else {
      # Резервный метод, если не нашли основной контент
      cat("Основной контент не найден, используем резервный метод\n")
      paragraphs <- html_content %>% html_nodes("p") %>% html_text(trim = TRUE)
      paragraphs <- paragraphs[nchar(paragraphs) > 50]
      article_text <- paste(paragraphs, collapse = " ")
    }
    
    # Вывод результатов
    separator <- paste(rep("=", 50), collapse = "")
    cat("\n", separator, "\n")
    cat("URL:", article_url, "\n")
    cat("Длина текста:", nchar(article_text), "символов\n")
    
    if (nchar(article_text) > 0) {
      # Проверяем наличие ключевого слова в тексте
      if (grepl("искусственный", article_text, ignore.case = TRUE)) {
        cat("Ключевое слово 'искусственный' найдено в тексте\n")
      } else {
        cat("Ключевое слово 'искусственный' НЕ найдено в тексте\n")
      }
      
      cat("Превью текста (первые 300 символов):\n")
      preview_text <- substr(article_text, 1, 300)
      cat(preview_text, "\n")
      if (nchar(article_text) > 300) cat("...\n")
    } else {
      cat("Текст не извлечен!\n")
    }
    cat(separator, "\n\n")
    
    return(article_text)
    
  }, error = function(e) {
    cat("Ошибка при извлечении текста из", article_url, ":", e$message, "\n")
    return("")
  })
}

# Функция для предобработки текста
preprocess_text <- function(text) {
  # Приводим к нижнему регистру
  text <- tolower(text)
  
  # Удаляем специальные символы, цифры, пунктуацию
  text <- str_replace_all(text, "[^[:alpha:][:space:]]", " ")
  text <- str_replace_all(text, "\\d+", " ")
  
  # Удаляем лишние пробелы
  text <- str_squish(text)
  
  text <- str_replace_all(text, "искусственн[а-я]+ интеллект", "интеллект")
  
  return(text)
}

create_tag_cloud <- function(texts, keyword, max_words = 50) {
  
  # загрузка библиотек
  if (!require("tm")) install.packages("tm"); library(tm)
  if (!require("stopwords")) install.packages("stopwords"); library(stopwords)
  if (!require("wordcloud")) install.packages("wordcloud"); library(wordcloud)
  if (!require("RColorBrewer")) install.packages("RColorBrewer"); library(RColorBrewer)
  if (!require("dplyr")) install.packages("dplyr"); library(dplyr)
  if (!require("udpipe")) install.packages("udpipe"); library(udpipe)
  
  model_file <- "russian-gsd-ud-2.5-191206.udpipe"
  
  if (!file.exists(model_file)) {
    cat("Скачиваем модель UDPIPE для русского языка...\n")
    udpipe_download_model(language = "russian", model_dir = ".", overwrite = TRUE)
    
    # Ищем реальное имя файла
    files <- list.files(pattern = "russian.*udpipe$")
    model_file <- files[1]
  }
  
  cat("Используется модель:", model_file, "\n")
  
  model <- udpipe_load_model(model_file)
  
  # СТОП-СЛОВА
  sm_stopwords <- stopwords(source = "smart")
  snowball_stopwords <- stopwords("ru", source = "snowball")
  stopwords_iso <- stopwords("ru", source = "stopwords-iso")
  stopwords_ntlk <- stopwords("ru", source = "nltk")
  stopwords_marimo <- stopwords("ru", source = "marimo")
  
  file_stopwords <- character(0)
  if (file.exists("stop-ru.txt")) {
    file_stopwords <- readLines("stop-ru.txt", encoding = "UTF-8")
    file_stopwords <- file_stopwords[file_stopwords != ""]
  }
  
  all_stopwords <- unique(c(
    sm_stopwords, snowball_stopwords, stopwords_iso,
    stopwords_ntlk, stopwords_marimo,
    tm::stopwords("russian"),
    tm::stopwords("english"),
    file_stopwords
  ))
  
  cat("Всего стоп-слов:", length(all_stopwords), "\n")
  
  # ЛЕММАТИЗАЦИЯ UDPIPE
  cat("Выполняется лемматизация...\n")
  
  all_text <- paste(texts, collapse = " ")
  
  ud <- udpipe_annotate(model, x = all_text)
  ud <- as.data.frame(ud)
  
  lemmas <- ud$lemma
  lemmas <- lemmas[!is.na(lemmas)]
  lemmas <- tolower(lemmas)
  
  # убираем стоп-слова
  lemmas <- lemmas[!lemmas %in% all_stopwords]
  lemmas <- lemmas[nchar(lemmas) >= 3]
  
  # убираем ключевое слово
  key_lemma <- udpipe_annotate(model, x = keyword)
  key_lemma <- as.data.frame(key_lemma)$lemma[1]
  lemmas <- lemmas[lemmas != key_lemma]
  
  # подсчёт частот
  freq <- table(lemmas)
  word_freq_df <- data.frame(
    word = names(freq),
    freq = as.numeric(freq),
    stringsAsFactors = FALSE
  ) %>% arrange(desc(freq))
  
  if (nrow(word_freq_df) > max_words) {
    word_freq_df <- word_freq_df[1:max_words, ]
  }
  
  cat("Топ 15 лемм:\n")
  print(head(word_freq_df, 15))
  
  # ---------- облако слов ----------
  if (nrow(word_freq_df) > 0) {
    png("tag_cloud_lemma.png", width = 1600, height = 1200, res = 150)
    par(mar = c(0, 0, 0, 0))
    
    set.seed(123)
    wordcloud(
      words = word_freq_df$word,
      freq = word_freq_df$freq,
      scale = c(5, 0.8),
      min.freq = 1,
      max.words = max_words,
      random.order = FALSE,
      rot.per = 0,
      colors = brewer.pal(8, "Dark2")
    )
    
    dev.off()
    cat("Облако сохранено в 'tag_cloud_lemma.png'\n")
  }
  
  return(word_freq_df)
}


# основная функция
perform_news_analysis <- function(base_url, search_url, keyword, max_articles) {
  cat("Начинаем анализ для ключевого слова:", keyword, "\n")
  
  # Шаг 1: Получаем ссылки на релевантные статьи
  cat("1. Поиск релевантных статей...\n")
  article_links <- get_search_results(search_url, keyword)
  
  if (length(article_links) == 0) {
    stop("Не найдено релевантных статей")
  }
  
  # Ограничиваем количество статей для анализа
  if (length(article_links) > max_articles) {
    article_links <- article_links[1:max_articles]
  }
  
  # Шаг 2: Извлекаем тексты статей
  cat("2. Извлечение текстов из", length(article_links), "статей...\n")
  article_texts <- character(0)
  
  for (i in seq_along(article_links)) {
    cat("Обрабатывается статья", i, "из", length(article_links), "\n")
    
    # Преобразуем относительные URL в абсолютные при необходимости
    if (str_detect(article_links[i], "^/")) {
      article_url <- paste0(base_url, article_links[i])
    } else if (!str_detect(article_links[i], "^http")) {
      article_url <- paste0(base_url, "/", article_links[i])
    } else {
      article_url <- article_links[i]
    }
    
    raw_text <- extract_article_text(article_url)
    
    # Очищаем текст с помощью preprocess_text()
    clean_text <- preprocess_text(raw_text)
    
    # Проверяем, что после очистки осталось что-то полезное
    if (nchar(clean_text) > 100) {
      article_texts <- c(article_texts, clean_text)
    }
    
    Sys.sleep(1)
  }
  
  if (length(article_texts) == 0) {
    stop("Не удалось извлечь тексты статей")
  }
  
  cat("Успешно извлечено", length(article_texts), "очищенных текстов статей\n")
  
  # Шаг 3: Создаем облако тегов
  cat("3. Создание облака тегов...\n")
  word_freq <- create_tag_cloud(article_texts, keyword)
  
  
  return(list(
    articles_processed = length(article_texts),
    top_words = head(word_freq, 10)
  ))
}

# Запуск анализа
base_url <- "https://gubdaily.ru"
search_url <- "https://gubdaily.ru/?s=искусственный+интеллект"
results <- perform_news_analysis(base_url, search_url, "искусственный", max_articles = 30)

