"""Curated content the demo dataset is assembled from. All companies and people are fictional.

A *track* is a typical role inside a specialization (e.g. "Go backend"): it fixes the stack and the
wording shared by resumes and vacancies, so candidates and vacancies of one track are comparable.
The track is exported with every record as ground truth for evaluating the matching.
"""

from dataclasses import dataclass

from app.models.enums import FspDiscipline, Grade, WorkFormat

A = FspDiscipline.ALGORITHMIC
P = FspDiscipline.PRODUCT
S = FspDiscipline.SECURITY
R = FspDiscipline.ROBOTICS
U = FspDiscipline.UAV


@dataclass(frozen=True, slots=True)
class Track:
    key: str
    specialization: str
    titles: tuple[str, ...]
    lead_titles: tuple[str, ...]
    core: tuple[str, ...]
    extra: tuple[str, ...]
    # Noun phrases (lowercase): resume focus and vacancy tasks.
    work: tuple[str, ...]
    requirements: tuple[str, ...]
    pluses: tuple[str, ...]
    fsp: tuple[tuple[FspDiscipline, float], ...]
    female_share: float
    fsp_bonus: float = 0.0
    domains: tuple[str, ...] = ()


TRACKS: tuple[Track, ...] = (
    # --- backend ---
    Track(
        key="python-backend",
        specialization="backend",
        titles=("Python-разработчик", "Backend-разработчик (Python)"),
        lead_titles=("Тимлид backend-команды (Python)", "Lead Python-разработчик"),
        core=("Python", "PostgreSQL"),
        extra=(
            "FastAPI",
            "Django",
            "Flask",
            "aiohttp",
            "SQLAlchemy",
            "Celery",
            "Redis",
            "RabbitMQ",
            "Kafka",
            "Docker",
            "Kubernetes",
            "pytest",
            "asyncio",
            "ClickHouse",
            "Elasticsearch",
            "gRPC",
            "Django REST Framework",
            "Pydantic",
        ),
        work=(
            "разработка асинхронных REST API на FastAPI",
            "проектирование схем данных и оптимизация запросов в PostgreSQL",
            "интеграции с внешними сервисами через очереди сообщений",
            "вынос модулей монолита на Django в отдельные сервисы",
            "фоновые задачи и планировщики на Celery",
            "покрытие кода тестами на pytest и настройка CI",
        ),
        requirements=(
            "понимание асинхронности в Python (asyncio)",
            "умение писать и оптимизировать SQL-запросы",
            "опыт работы с Docker и понимание основ CI/CD",
            "знание принципов проектирования REST API",
        ),
        pluses=(
            "опыт с Kafka или RabbitMQ",
            "опыт работы с ClickHouse",
            "понимание Kubernetes на уровне пользователя",
            "опыт профилирования и оптимизации Python-кода",
        ),
        fsp=((A, 0.5), (P, 0.45), (S, 0.05)),
        female_share=0.2,
    ),
    Track(
        key="go-backend",
        specialization="backend",
        titles=("Go-разработчик", "Backend-разработчик (Go)"),
        lead_titles=("Тимлид backend-команды (Go)", "Lead Go-разработчик"),
        core=("Go", "PostgreSQL"),
        extra=(
            "gRPC",
            "Kafka",
            "Redis",
            "Docker",
            "Kubernetes",
            "ClickHouse",
            "Prometheus",
            "NATS",
            "MongoDB",
            "Protobuf",
            "Gin",
            "sqlx",
            "OpenTelemetry",
            "Grafana",
            "Микросервисы",
        ),
        work=(
            "разработка высоконагруженных микросервисов на Go",
            "проектирование gRPC-контрактов между сервисами",
            "обработка событий из Kafka в реальном времени",
            "оптимизация задержек и потребления памяти сервисов",
            "настройка метрик и трассировки (Prometheus, OpenTelemetry)",
            "перенос легаси-сервисов с PHP и Python на Go",
        ),
        requirements=(
            "понимание конкурентности в Go: горутины, каналы, context",
            "опыт проектирования микросервисной архитектуры",
            "уверенная работа с PostgreSQL и индексами",
            "опыт работы с брокерами сообщений",
        ),
        pluses=(
            "опыт с ClickHouse или другими колоночными БД",
            "опыт эксплуатации сервисов в Kubernetes",
            "контрибьюты в open source на Go",
            "опыт highload-проектов с нагрузкой от 10k RPS",
        ),
        fsp=((A, 0.6), (P, 0.35), (S, 0.05)),
        female_share=0.15,
        fsp_bonus=0.05,
    ),
    Track(
        key="java-backend",
        specialization="backend",
        titles=("Java-разработчик", "Backend-разработчик (Java)"),
        lead_titles=("Тимлид Java-команды", "Lead Java-разработчик"),
        core=("Java", "Spring Boot"),
        extra=(
            "Spring Cloud",
            "Hibernate",
            "PostgreSQL",
            "Oracle",
            "Kafka",
            "RabbitMQ",
            "Docker",
            "Kubernetes",
            "Maven",
            "Gradle",
            "JUnit",
            "Redis",
            "Микросервисы",
            "Camunda",
            "Liquibase",
        ),
        work=(
            "разработка микросервисов на Spring Boot",
            "интеграция с внутренними системами через Kafka",
            "проектирование REST API и контрактов между командами",
            "оптимизация работы с базой данных через Hibernate",
            "автоматизация бизнес-процессов на Camunda",
            "модульные и интеграционные тесты",
        ),
        requirements=(
            "уверенное знание Java 17+ и Spring",
            "понимание ООП, SOLID и паттернов проектирования",
            "опыт работы с реляционными БД и транзакциями",
            "опыт работы с Git и код-ревью",
        ),
        pluses=(
            "опыт с Kotlin",
            "знание Spring Cloud и паттернов распределённых систем",
            "опыт работы в банковском или финтех-домене",
            "опыт с Testcontainers",
        ),
        fsp=((A, 0.55), (P, 0.45)),
        female_share=0.2,
    ),
    Track(
        key="kotlin-backend",
        specialization="backend",
        titles=("Kotlin-разработчик", "Backend-разработчик (Kotlin)"),
        lead_titles=("Тимлид backend-команды (Kotlin)",),
        core=("Kotlin", "Spring Boot"),
        extra=(
            "Ktor",
            "PostgreSQL",
            "Kafka",
            "Coroutines",
            "Docker",
            "Kubernetes",
            "Gradle",
            "Exposed",
            "Redis",
            "gRPC",
            "JUnit",
        ),
        work=(
            "разработка сервисов на Kotlin и Spring Boot",
            "перевод сервисов с Java на Kotlin",
            "асинхронная обработка событий на корутинах",
            "проектирование API для мобильных клиентов",
            "оптимизация запросов к PostgreSQL",
        ),
        requirements=(
            "опыт коммерческой разработки на Kotlin или Java",
            "понимание корутин и асинхронного программирования",
            "опыт работы с PostgreSQL",
            "умение писать тесты",
        ),
        pluses=(
            "опыт с Ktor",
            "опыт работы с Kafka",
            "интерес к функциональному программированию",
        ),
        fsp=((A, 0.5), (P, 0.5)),
        female_share=0.15,
    ),
    Track(
        key="dotnet-backend",
        specialization="backend",
        titles=(".NET-разработчик", "C#-разработчик"),
        lead_titles=("Тимлид .NET-команды",),
        core=("C#", "ASP.NET Core"),
        extra=(
            "Entity Framework Core",
            "MS SQL Server",
            "PostgreSQL",
            "RabbitMQ",
            "Docker",
            "Redis",
            "SignalR",
            "xUnit",
            "gRPC",
            "MassTransit",
            "Kubernetes",
        ),
        work=(
            "разработка веб-сервисов на ASP.NET Core",
            "интеграция с внешними системами через RabbitMQ",
            "оптимизация запросов Entity Framework",
            "перевод сервисов с .NET Framework на современный .NET",
            "уведомления в реальном времени на SignalR",
        ),
        requirements=(
            "уверенное знание C# и .NET 6+",
            "опыт работы с Entity Framework Core",
            "понимание SOLID и принципов чистой архитектуры",
            "опыт работы с реляционными БД",
        ),
        pluses=(
            "опыт с MassTransit",
            "опыт работы с Kubernetes",
            "знание промышленных протоколов (OPC UA, MQTT)",
        ),
        fsp=((A, 0.5), (P, 0.5)),
        female_share=0.2,
    ),
    Track(
        key="php-backend",
        specialization="backend",
        titles=("PHP-разработчик", "Backend-разработчик (PHP)"),
        lead_titles=("Тимлид PHP-команды",),
        core=("PHP", "MySQL"),
        extra=(
            "Laravel",
            "Symfony",
            "Redis",
            "RabbitMQ",
            "Docker",
            "PostgreSQL",
            "Elasticsearch",
            "Nginx",
            "PHPUnit",
            "Composer",
            "Doctrine",
        ),
        work=(
            "разработка backend интернет-магазина на Laravel",
            "проектирование REST API для мобильного приложения",
            "рефакторинг легаси-кода и покрытие его тестами",
            "интеграции с платёжными системами и службами доставки",
            "оптимизация медленных запросов к MySQL",
        ),
        requirements=(
            "опыт коммерческой разработки на PHP 8",
            "уверенное знание Laravel или Symfony",
            "умение оптимизировать SQL-запросы",
            "опыт работы с Git и Docker",
        ),
        pluses=(
            "опыт с Elasticsearch",
            "опыт работы с очередями (RabbitMQ)",
            "опыт разработки на Go",
        ),
        fsp=((A, 0.3), (P, 0.7)),
        female_share=0.25,
    ),
    Track(
        key="node-backend",
        specialization="backend",
        titles=("Node.js-разработчик", "Backend-разработчик (Node.js)"),
        lead_titles=("Тимлид backend-команды (Node.js)",),
        core=("Node.js", "TypeScript"),
        extra=(
            "NestJS",
            "Express",
            "PostgreSQL",
            "MongoDB",
            "Redis",
            "GraphQL",
            "Kafka",
            "Docker",
            "Prisma",
            "TypeORM",
            "Jest",
            "RabbitMQ",
            "WebSocket",
        ),
        work=(
            "разработка сервисов на NestJS",
            "проектирование GraphQL API",
            "функциональность реального времени на WebSocket",
            "интеграции со сторонними API и вебхуками",
            "оптимизация производительности Node.js-сервисов",
        ),
        requirements=(
            "уверенное знание TypeScript и Node.js",
            "опыт работы с NestJS или Express",
            "понимание event loop и асинхронности",
            "опыт работы с PostgreSQL или MongoDB",
        ),
        pluses=(
            "опыт с GraphQL",
            "опыт работы с микросервисной архитектурой",
            "опыт написания e2e-тестов",
        ),
        fsp=((A, 0.3), (P, 0.7)),
        female_share=0.25,
    ),
    Track(
        key="cpp-backend",
        specialization="backend",
        titles=("C++-разработчик", "Разработчик C++ (Linux)"),
        lead_titles=("Тимлид команды C++",),
        core=("C++", "Linux"),
        extra=(
            "STL",
            "Boost",
            "CMake",
            "gRPC",
            "Многопоточность",
            "Python",
            "Docker",
            "GDB",
            "Qt",
            "ROS 2",
            "PostgreSQL",
        ),
        work=(
            "разработка высокопроизводительных модулей на C++20",
            "оптимизация алгоритмов и работы с памятью",
            "разработка многопоточных сетевых сервисов",
            "бортовое ПО и симуляторы",
            "профилирование и поиск узких мест",
        ),
        requirements=(
            "уверенное знание C++17/20 и STL",
            "понимание многопоточности и модели памяти",
            "опыт разработки под Linux",
            "сильная алгоритмическая подготовка",
        ),
        pluses=(
            "опыт с ROS 2",
            "опыт работы со встраиваемыми системами",
            "призовые места в олимпиадах по программированию",
        ),
        fsp=((A, 0.5), (R, 0.25), (U, 0.25)),
        female_share=0.1,
        fsp_bonus=0.15,
    ),
    Track(
        key="rust-backend",
        specialization="backend",
        titles=("Rust-разработчик", "Backend-разработчик (Rust)"),
        lead_titles=("Тимлид backend-команды (Rust)",),
        core=("Rust", "Tokio"),
        extra=(
            "Axum",
            "Actix Web",
            "PostgreSQL",
            "gRPC",
            "Kafka",
            "Docker",
            "Linux",
            "WebAssembly",
            "Redis",
            "FFmpeg",
        ),
        work=(
            "разработка высоконагруженных сервисов на Rust",
            "переписывание критичных компонентов с C++ на Rust",
            "асинхронная обработка потоков данных на Tokio",
            "обработка видеопотоков в медиасервере",
        ),
        requirements=(
            "опыт коммерческой разработки на Rust",
            "понимание ownership, lifetimes и async Rust",
            "опыт разработки сетевых сервисов",
            "уверенная работа в Linux",
        ),
        pluses=(
            "опыт с FFmpeg и видеокодеками",
            "опыт с WebAssembly",
            "контрибьюты в open source",
        ),
        fsp=((A, 0.7), (P, 0.3)),
        female_share=0.1,
        fsp_bonus=0.1,
    ),
    # --- frontend ---
    Track(
        key="react-frontend",
        specialization="frontend",
        titles=("Frontend-разработчик (React)", "React-разработчик"),
        lead_titles=("Тимлид frontend-команды", "Lead Frontend-разработчик"),
        core=("TypeScript", "React"),
        extra=(
            "Redux Toolkit",
            "TanStack Query",
            "Next.js",
            "Vite",
            "Webpack",
            "CSS Modules",
            "Tailwind CSS",
            "SCSS",
            "Jest",
            "Vitest",
            "Storybook",
            "Playwright",
            "MobX",
            "Zustand",
            "GraphQL",
            "Figma",
        ),
        work=(
            "разработка интерфейсов на React и TypeScript",
            "развитие дизайн-системы в Storybook",
            "оптимизация производительности и Web Vitals",
            "перевод сборки с Webpack на Vite",
            "серверный рендеринг на Next.js",
            "тестирование компонентов",
        ),
        requirements=(
            "уверенное знание TypeScript и React",
            "опыт работы со стейт-менеджерами (Redux Toolkit, MobX или Zustand)",
            "понимание адаптивной вёрстки и доступности",
            "опыт работы с REST API",
        ),
        pluses=(
            "опыт с Next.js",
            "опыт e2e-тестирования на Playwright",
            "опыт развития дизайн-системы",
            "понимание того, как браузер отрисовывает страницу",
        ),
        fsp=((P, 0.85), (A, 0.15)),
        female_share=0.4,
    ),
    Track(
        key="vue-frontend",
        specialization="frontend",
        titles=("Frontend-разработчик (Vue)", "Vue-разработчик"),
        lead_titles=("Тимлид frontend-команды (Vue)",),
        core=("TypeScript", "Vue 3"),
        extra=(
            "Nuxt",
            "Pinia",
            "Vuex",
            "Vite",
            "SCSS",
            "Vitest",
            "Cypress",
            "Element Plus",
            "Webpack",
            "Figma",
            "Tailwind CSS",
        ),
        work=(
            "разработка интерфейсов на Vue 3 и Composition API",
            "переезд с Vue 2 на Vue 3",
            "разработка SSR-приложения на Nuxt",
            "вёрстка сложных форм и таблиц",
            "интеграция с REST API и обработка ошибок",
        ),
        requirements=(
            "уверенное знание Vue 3 и Composition API",
            "опыт работы с TypeScript",
            "опыт адаптивной вёрстки",
            "понимание HTTP и REST",
        ),
        pluses=(
            "опыт с Nuxt",
            "опыт тестирования на Vitest или Cypress",
            "опыт работы с дизайн-системой",
        ),
        fsp=((P, 0.85), (A, 0.15)),
        female_share=0.4,
    ),
    Track(
        key="angular-frontend",
        specialization="frontend",
        titles=("Frontend-разработчик (Angular)", "Angular-разработчик"),
        lead_titles=("Тимлид frontend-команды (Angular)",),
        core=("TypeScript", "Angular"),
        extra=(
            "RxJS",
            "NgRx",
            "Angular Material",
            "Jest",
            "SCSS",
            "Nx",
            "Webpack",
            "Storybook",
            "Karma",
        ),
        work=(
            "разработка корпоративных интерфейсов на Angular",
            "управление состоянием на NgRx",
            "библиотека переиспользуемых компонентов",
            "реактивная работа с данными на RxJS",
            "оптимизация change detection",
        ),
        requirements=(
            "опыт коммерческой разработки на Angular 12+",
            "уверенное знание RxJS",
            "опыт работы с TypeScript",
            "понимание модульной архитектуры приложений",
        ),
        pluses=(
            "опыт с NgRx",
            "опыт работы с Nx-монорепозиторием",
            "опыт разработки дашбордов и графиков",
        ),
        fsp=((P, 0.85), (A, 0.15)),
        female_share=0.35,
    ),
    # --- fullstack ---
    Track(
        key="ts-fullstack",
        specialization="fullstack",
        titles=("Fullstack-разработчик (TypeScript)", "Fullstack-разработчик (React + Node.js)"),
        lead_titles=("Тимлид fullstack-команды",),
        core=("TypeScript", "React", "Node.js"),
        extra=(
            "NestJS",
            "Next.js",
            "PostgreSQL",
            "Prisma",
            "Docker",
            "GraphQL",
            "Redis",
            "Tailwind CSS",
            "tRPC",
            "MongoDB",
            "Jest",
        ),
        work=(
            "разработка фич от схемы БД до интерфейса",
            "API на NestJS и клиентская часть на React",
            "серверный рендеринг на Next.js",
            "настройка CI/CD и деплоя в облако",
            "интеграции с внешними сервисами",
        ),
        requirements=(
            "опыт разработки на TypeScript и на фронтенде, и на бэкенде",
            "опыт работы с React",
            "опыт проектирования REST или GraphQL API",
            "уверенная работа с PostgreSQL",
        ),
        pluses=(
            "опыт с Next.js",
            "опыт работы с Docker и облачной инфраструктурой",
            "опыт запуска продукта с нуля",
        ),
        fsp=((P, 0.8), (A, 0.2)),
        female_share=0.25,
    ),
    Track(
        key="python-fullstack",
        specialization="fullstack",
        titles=("Fullstack-разработчик (Python + React)",),
        lead_titles=("Тимлид fullstack-команды (Python)",),
        core=("Python", "React"),
        extra=(
            "Django",
            "FastAPI",
            "PostgreSQL",
            "TypeScript",
            "Docker",
            "Celery",
            "Redis",
            "Nginx",
            "Django REST Framework",
        ),
        work=(
            "разработка внутренних сервисов на Django и React",
            "проектирование API и клиентских интерфейсов",
            "автоматизация отчётов и выгрузок",
            "поддержка админ-панелей и личных кабинетов",
        ),
        requirements=(
            "опыт разработки на Python (Django или FastAPI)",
            "опыт разработки интерфейсов на React",
            "умение работать с SQL",
            "понимание принципов REST",
        ),
        pluses=(
            "опыт с TypeScript",
            "опыт с Celery",
            "опыт деплоя на Linux-серверы",
        ),
        fsp=((P, 0.75), (A, 0.25)),
        female_share=0.25,
    ),
    Track(
        key="php-fullstack",
        specialization="fullstack",
        titles=("Fullstack-разработчик (PHP + Vue)",),
        lead_titles=("Тимлид fullstack-команды (PHP)",),
        core=("PHP", "Laravel", "Vue 3"),
        extra=(
            "MySQL",
            "Redis",
            "Docker",
            "Inertia.js",
            "Tailwind CSS",
            "TypeScript",
            "PHPUnit",
        ),
        work=(
            "разработка личных кабинетов и CRM на Laravel и Vue",
            "интеграции с 1С и платёжными сервисами",
            "доработка админ-панелей",
            "оптимизация загрузки страниц",
        ),
        requirements=(
            "опыт разработки на PHP 8 и Laravel",
            "опыт разработки на Vue",
            "умение работать с MySQL",
            "опыт работы с Git",
        ),
        pluses=(
            "опыт с Inertia.js",
            "опыт интеграций с 1С",
            "опыт с TypeScript",
        ),
        fsp=((P, 0.8), (A, 0.2)),
        female_share=0.3,
    ),
    # --- mobile ---
    Track(
        key="ios",
        specialization="mobile",
        titles=("iOS-разработчик",),
        lead_titles=("Тимлид iOS-команды", "Руководитель мобильной разработки"),
        core=("Swift", "UIKit"),
        extra=(
            "SwiftUI",
            "Combine",
            "Swift Concurrency",
            "Core Data",
            "Alamofire",
            "XCTest",
            "Swift Package Manager",
            "MVVM",
            "VIPER",
            "Realm",
            "Firebase",
            "Fastlane",
        ),
        work=(
            "разработка новых экранов на SwiftUI",
            "переход с UIKit на SwiftUI",
            "оптимизация запуска и потребления памяти приложения",
            "модуляризация и вынос фич в SPM-пакеты",
            "интеграция платёжных SDK и push-уведомлений",
        ),
        requirements=(
            "уверенное знание Swift и UIKit",
            "опыт работы со SwiftUI",
            "понимание многопоточности в iOS (GCD, Swift Concurrency)",
            "опыт публикации приложений в App Store",
        ),
        pluses=(
            "опыт с Combine",
            "опыт настройки CI на Fastlane",
            "опыт модуляризации крупного приложения",
        ),
        fsp=((P, 0.85), (A, 0.15)),
        female_share=0.2,
    ),
    Track(
        key="android",
        specialization="mobile",
        titles=("Android-разработчик",),
        lead_titles=("Тимлид Android-команды", "Руководитель мобильной разработки"),
        core=("Kotlin", "Android SDK"),
        extra=(
            "Jetpack Compose",
            "Coroutines",
            "Flow",
            "Room",
            "Hilt",
            "Dagger 2",
            "Retrofit",
            "MVVM",
            "Clean Architecture",
            "Gradle",
            "JUnit",
            "Espresso",
            "Firebase",
            "RxJava",
        ),
        work=(
            "разработка экранов на Jetpack Compose",
            "перевод проекта с RxJava на корутины",
            "работа приложения в фоне и в офлайн-режиме",
            "многомодульная архитектура и ускорение сборки",
            "интеграция карт и геолокации",
        ),
        requirements=(
            "уверенное знание Kotlin и Android SDK",
            "опыт работы с Jetpack Compose",
            "понимание корутин и Flow",
            "опыт публикации приложений в RuStore или Google Play",
        ),
        pluses=(
            "опыт с картографическими SDK",
            "опыт написания UI-тестов",
            "опыт оптимизации энергопотребления",
        ),
        fsp=((P, 0.85), (A, 0.15)),
        female_share=0.2,
    ),
    Track(
        key="flutter",
        specialization="mobile",
        titles=("Flutter-разработчик",),
        lead_titles=("Тимлид мобильной команды (Flutter)",),
        core=("Dart", "Flutter"),
        extra=(
            "BLoC",
            "Riverpod",
            "Provider",
            "Firebase",
            "Dio",
            "Hive",
            "GetX",
            "Codemagic",
            "Kotlin",
            "Swift",
        ),
        work=(
            "кроссплатформенная разработка приложений на Flutter",
            "архитектура на BLoC",
            "интеграция нативных модулей Android и iOS",
            "оптимизация анимаций и отрисовки",
        ),
        requirements=(
            "опыт коммерческой разработки на Flutter",
            "понимание BLoC или Riverpod",
            "опыт публикации приложений в сторах",
            "опыт работы с REST API",
        ),
        pluses=(
            "опыт нативной разработки на Kotlin или Swift",
            "опыт с Codemagic",
            "опыт работы с картами",
        ),
        fsp=((P, 0.85), (A, 0.15)),
        female_share=0.2,
    ),
    Track(
        key="react-native",
        specialization="mobile",
        titles=("React Native-разработчик",),
        lead_titles=("Тимлид мобильной команды (React Native)",),
        core=("TypeScript", "React Native"),
        extra=(
            "Redux Toolkit",
            "Expo",
            "MobX",
            "React Navigation",
            "Jest",
            "Detox",
            "Firebase",
            "Reanimated",
        ),
        work=(
            "разработка кроссплатформенного приложения на React Native",
            "оптимизация производительности списков и анимаций",
            "интеграция нативных модулей",
            "настройка OTA-обновлений",
        ),
        requirements=(
            "опыт коммерческой разработки на React Native",
            "уверенное знание TypeScript",
            "понимание жизненного цикла мобильного приложения",
            "опыт публикации в сторах",
        ),
        pluses=(
            "опыт нативной разработки",
            "опыт с Detox",
            "опыт с Reanimated",
        ),
        fsp=((P, 0.85), (A, 0.15)),
        female_share=0.25,
    ),
    # --- data science ---
    Track(
        key="ml-classic",
        specialization="data-science",
        titles=("Data Scientist", "ML-инженер"),
        lead_titles=("Lead Data Scientist", "Руководитель группы машинного обучения"),
        core=("Python", "pandas", "scikit-learn"),
        extra=(
            "NumPy",
            "CatBoost",
            "LightGBM",
            "XGBoost",
            "SQL",
            "Matplotlib",
            "Jupyter",
            "MLflow",
            "Optuna",
            "A/B-тестирование",
            "statsmodels",
            "Airflow",
            "Docker",
            "PySpark",
            "ClickHouse",
        ),
        work=(
            "модели прогнозирования спроса",
            "рекомендательные системы",
            "проведение и анализ A/B-тестов",
            "вывод моделей в продакшен и мониторинг их качества",
            "feature engineering на больших табличных данных",
        ),
        requirements=(
            "уверенное знание Python и классических ML-алгоритмов",
            "хорошая математическая подготовка (статистика, теория вероятностей)",
            "умение писать SQL-запросы",
            "опыт вывода моделей в продакшен",
        ),
        pluses=(
            "опыт с рекомендательными системами",
            "опыт работы с PySpark",
            "призовые места в соревнованиях по анализу данных",
        ),
        fsp=((A, 0.5), (P, 0.45), (U, 0.05)),
        female_share=0.35,
        fsp_bonus=0.05,
    ),
    Track(
        key="ml-cv",
        specialization="data-science",
        titles=("ML-инженер (Computer Vision)", "CV-инженер"),
        lead_titles=("Руководитель группы компьютерного зрения",),
        core=("Python", "PyTorch", "OpenCV"),
        extra=(
            "NumPy",
            "Albumentations",
            "YOLO",
            "ONNX",
            "TensorRT",
            "Triton Inference Server",
            "CUDA",
            "Docker",
            "FastAPI",
            "MLflow",
            "ClearML",
        ),
        work=(
            "обучение моделей детекции и сегментации",
            "подготовка и разметка датасетов",
            "оптимизация инференса с помощью ONNX и TensorRT",
            "развёртывание моделей на Triton Inference Server",
            "исследование новых архитектур нейросетей",
        ),
        requirements=(
            "опыт обучения нейросетей на PyTorch",
            "понимание архитектур CNN и трансформеров для CV",
            "опыт работы с OpenCV",
            "умение работать с GPU и CUDA",
        ),
        pluses=(
            "опыт оптимизации моделей под edge-устройства",
            "публикации или участие в соревнованиях по CV",
            "опыт работы с медицинскими изображениями",
        ),
        fsp=((A, 0.45), (P, 0.35), (U, 0.2)),
        female_share=0.25,
        fsp_bonus=0.05,
    ),
    Track(
        key="ml-nlp",
        specialization="data-science",
        titles=("NLP-инженер", "ML-инженер (NLP/LLM)"),
        lead_titles=("Руководитель NLP-направления",),
        core=("Python", "PyTorch", "Hugging Face Transformers"),
        extra=(
            "LangChain",
            "vLLM",
            "FAISS",
            "Qdrant",
            "FastAPI",
            "Docker",
            "spaCy",
            "RAG",
            "LoRA",
            "MLflow",
            "Elasticsearch",
        ),
        work=(
            "дообучение языковых моделей под задачи клиентов",
            "RAG-пайплайны для поиска по документам",
            "оценка качества LLM и борьба с галлюцинациями",
            "оптимизация инференса LLM на vLLM",
            "сбор и разметка датасетов для NLP",
        ),
        requirements=(
            "опыт работы с трансформерами и Hugging Face",
            "понимание принципов работы LLM и RAG",
            "уверенное знание Python и PyTorch",
            "опыт вывода моделей в продакшен",
        ),
        pluses=(
            "опыт дообучения моделей с LoRA",
            "опыт работы с векторными БД",
            "публикации на профильных конференциях",
        ),
        fsp=((A, 0.55), (P, 0.45)),
        female_share=0.3,
        fsp_bonus=0.05,
    ),
    Track(
        key="product-analytics",
        specialization="data-science",
        titles=("Аналитик данных", "Продуктовый аналитик"),
        lead_titles=("Руководитель отдела аналитики",),
        core=("SQL", "Python"),
        extra=(
            "pandas",
            "ClickHouse",
            "Superset",
            "DataLens",
            "A/B-тестирование",
            "Excel",
            "Математическая статистика",
            "Airflow",
            "Metabase",
            "Jupyter",
            "PostgreSQL",
        ),
        work=(
            "дашборды для продуктовых команд",
            "анализ воронок и когорт пользователей",
            "дизайн и анализ A/B-тестов",
            "поиск точек роста продукта",
            "автоматизация отчётности",
        ),
        requirements=(
            "уверенное знание SQL (оконные функции, CTE)",
            "знание Python для анализа данных",
            "понимание математической статистики",
            "опыт построения дашбордов",
        ),
        pluses=(
            "опыт работы с ClickHouse",
            "опыт с DataLens или Superset",
            "продуктовое мышление",
        ),
        fsp=((P, 0.65), (A, 0.35)),
        female_share=0.5,
    ),
    # --- data engineering ---
    Track(
        key="de-batch",
        specialization="data-engineering",
        titles=("Data Engineer", "Инженер данных"),
        lead_titles=("Lead Data Engineer", "Руководитель группы инженеров данных"),
        core=("Python", "SQL", "Apache Airflow"),
        extra=(
            "Apache Spark",
            "Hadoop",
            "Hive",
            "ClickHouse",
            "Greenplum",
            "PostgreSQL",
            "dbt",
            "Kafka",
            "Docker",
            "Scala",
            "Trino",
            "S3",
            "Apache Iceberg",
        ),
        work=(
            "ETL/ELT-пайплайны на Airflow",
            "построение хранилища данных и витрин",
            "оптимизация Spark-джобов",
            "миграция DWH с Greenplum на ClickHouse",
            "контроль качества данных",
        ),
        requirements=(
            "опыт разработки пайплайнов на Airflow",
            "уверенное знание SQL и принципов моделирования данных",
            "опыт работы со Spark",
            "понимание принципов построения DWH",
        ),
        pluses=(
            "опыт с dbt",
            "опыт с Data Vault или Anchor Modeling",
            "знание Scala",
        ),
        fsp=((A, 0.4), (P, 0.6)),
        female_share=0.25,
    ),
    Track(
        key="de-stream",
        specialization="data-engineering",
        titles=("Data Engineer (стриминг)", "Инженер данных (потоковая обработка)"),
        lead_titles=("Lead Data Engineer (стриминг)",),
        core=("Kafka", "Apache Flink", "Python"),
        extra=(
            "Scala",
            "Java",
            "ClickHouse",
            "Kafka Streams",
            "Debezium",
            "Spark Streaming",
            "Docker",
            "Kubernetes",
            "PostgreSQL",
            "Avro",
        ),
        work=(
            "потоковые пайплайны на Flink",
            "обработка телеметрии в реальном времени",
            "CDC-репликация из PostgreSQL через Debezium",
            "проектирование схем событий и управление ими",
        ),
        requirements=(
            "опыт работы с Kafka",
            "опыт разработки на Flink или Spark Streaming",
            "знание Python, Scala или Java",
            "понимание семантики exactly-once и обработки опоздавших событий",
        ),
        pluses=(
            "опыт с Debezium",
            "опыт с ClickHouse",
            "опыт эксплуатации Kafka-кластеров",
        ),
        fsp=((A, 0.4), (P, 0.6)),
        female_share=0.2,
    ),
    # --- devops ---
    Track(
        key="devops",
        specialization="devops",
        titles=("DevOps-инженер", "Инженер инфраструктуры"),
        lead_titles=("Руководитель DevOps-направления", "Lead DevOps-инженер"),
        core=("Linux", "Docker", "Kubernetes"),
        extra=(
            "Terraform",
            "Ansible",
            "GitLab CI",
            "GitHub Actions",
            "Helm",
            "Argo CD",
            "Prometheus",
            "Grafana",
            "ELK",
            "Nginx",
            "Bash",
            "Python",
            "Yandex Cloud",
            "HashiCorp Vault",
            "PostgreSQL",
        ),
        work=(
            "поддержка и развитие Kubernetes-кластеров",
            "автоматизация инфраструктуры через Terraform и Ansible",
            "CI/CD-пайплайны в GitLab CI",
            "мониторинг и алертинг",
            "переезд сервисов в облако",
        ),
        requirements=(
            "уверенное администрирование Linux",
            "опыт эксплуатации Kubernetes в продакшене",
            "опыт с Terraform или Ansible",
            "опыт настройки CI/CD",
        ),
        pluses=(
            "опыт с Argo CD",
            "опыт работы с Yandex Cloud",
            "навыки программирования на Python или Go",
        ),
        fsp=((P, 0.5), (S, 0.4), (A, 0.1)),
        female_share=0.1,
        fsp_bonus=-0.05,
    ),
    Track(
        key="sre",
        specialization="devops",
        titles=("SRE-инженер", "Site Reliability Engineer"),
        lead_titles=("Руководитель группы SRE",),
        core=("Linux", "Kubernetes", "Prometheus"),
        extra=(
            "Grafana",
            "Go",
            "Python",
            "Terraform",
            "VictoriaMetrics",
            "Loki",
            "Jaeger",
            "OpenTelemetry",
            "Kafka",
            "PostgreSQL",
            "Patroni",
            "HAProxy",
        ),
        work=(
            "обеспечение доступности сервисов на уровне 99,95%",
            "разбор инцидентов и постмортемы",
            "внедрение SLO и error budget",
            "observability-стек: метрики, логи, трассировки",
            "планирование мощностей и нагрузочные тесты",
        ),
        requirements=(
            "опыт эксплуатации высоконагруженных систем",
            "глубокое знание Linux и сетей",
            "опыт работы с Prometheus и Grafana",
            "умение программировать на Go или Python",
        ),
        pluses=(
            "опыт с Patroni и отказоустойчивым PostgreSQL",
            "опыт с OpenTelemetry",
            "опыт дежурств и управления инцидентами",
        ),
        fsp=((A, 0.3), (P, 0.4), (S, 0.3)),
        female_share=0.1,
    ),
    # --- qa ---
    Track(
        key="qa-manual",
        specialization="qa",
        titles=("QA-инженер", "Тестировщик ПО"),
        lead_titles=("Руководитель отдела тестирования", "QA Lead"),
        core=("Тест-дизайн", "Jira"),
        extra=(
            "TestRail",
            "Qase",
            "Postman",
            "SQL",
            "Charles Proxy",
            "Chrome DevTools",
            "Swagger",
            "Allure TestOps",
            "Confluence",
            "Kibana",
            "Мобильное тестирование",
            "API-тестирование",
        ),
        work=(
            "функциональное и регрессионное тестирование веб-приложения",
            "тестирование API через Postman",
            "написание и актуализация тест-кейсов",
            "тестирование мобильных приложений",
            "анализ логов и локализация дефектов",
        ),
        requirements=(
            "знание техник тест-дизайна",
            "опыт тестирования веб-приложений",
            "умение работать с Postman и DevTools",
            "базовое знание SQL",
        ),
        pluses=(
            "опыт тестирования мобильных приложений",
            "опыт работы с Charles Proxy",
            "желание развиваться в автоматизации",
        ),
        fsp=((P, 0.9), (S, 0.1)),
        female_share=0.55,
        fsp_bonus=-0.1,
    ),
    Track(
        key="qa-auto-python",
        specialization="qa",
        titles=("QA Automation-инженер (Python)", "Инженер по автоматизации тестирования"),
        lead_titles=("QA Automation Lead",),
        core=("Python", "pytest"),
        extra=(
            "Selenium",
            "Playwright",
            "Requests",
            "Allure",
            "Docker",
            "GitLab CI",
            "Postman",
            "SQL",
            "Locust",
            "Appium",
            "Jenkins",
        ),
        work=(
            "автоматизация тестирования API и UI на pytest",
            "разработка фреймворка автотестов с нуля",
            "встраивание автотестов в CI/CD",
            "нагрузочное тестирование на Locust",
        ),
        requirements=(
            "опыт автоматизации тестирования на Python",
            "уверенное знание pytest",
            "опыт с Selenium или Playwright",
            "понимание клиент-серверной архитектуры",
        ),
        pluses=(
            "опыт с Allure TestOps",
            "опыт нагрузочного тестирования",
            "опыт с Docker",
        ),
        fsp=((P, 0.9), (S, 0.1)),
        female_share=0.4,
        fsp_bonus=-0.1,
    ),
    Track(
        key="qa-auto-java",
        specialization="qa",
        titles=("QA Automation-инженер (Java)",),
        lead_titles=("QA Automation Lead (Java)",),
        core=("Java", "JUnit 5"),
        extra=(
            "Selenide",
            "Selenium",
            "REST Assured",
            "Allure",
            "Maven",
            "Gradle",
            "Jenkins",
            "Appium",
            "Kafka",
            "SQL",
            "Docker",
            "TestNG",
        ),
        work=(
            "автоматизация тестирования REST API на REST Assured",
            "UI-автотесты на Selenide",
            "тестирование интеграций через Kafka",
            "отчётность о качестве в Allure",
        ),
        requirements=(
            "опыт автоматизации тестирования на Java",
            "знание JUnit 5 или TestNG",
            "опыт работы с REST Assured",
            "знание SQL",
        ),
        pluses=(
            "опыт тестирования через Kafka",
            "опыт с Appium",
            "опыт настройки Jenkins",
        ),
        fsp=((P, 0.85), (A, 0.15)),
        female_share=0.4,
        fsp_bonus=-0.1,
    ),
    Track(
        key="qa-auto-ts",
        specialization="qa",
        titles=("QA Automation-инженер (TypeScript)",),
        lead_titles=("QA Automation Lead (TypeScript)",),
        core=("TypeScript", "Playwright"),
        extra=(
            "Cypress",
            "Jest",
            "Allure",
            "GitHub Actions",
            "k6",
            "Docker",
            "Postman",
        ),
        work=(
            "e2e-тесты на Playwright",
            "визуальное регрессионное тестирование",
            "запуск тестов в CI на каждый merge request",
            "нагрузочные тесты на k6",
        ),
        requirements=(
            "опыт автоматизации на TypeScript или JavaScript",
            "опыт с Playwright или Cypress",
            "понимание пирамиды тестирования",
            "опыт работы с CI",
        ),
        pluses=(
            "опыт с k6",
            "опыт тестирования доступности",
            "опыт работы с моками API",
        ),
        fsp=((P, 0.9), (A, 0.1)),
        female_share=0.4,
        fsp_bonus=-0.1,
    ),
    Track(
        key="qa-load",
        specialization="qa",
        titles=("Инженер по нагрузочному тестированию",),
        lead_titles=("Руководитель группы нагрузочного тестирования",),
        core=("JMeter", "Grafana"),
        extra=(
            "Gatling",
            "k6",
            "InfluxDB",
            "Python",
            "Scala",
            "Locust",
            "Prometheus",
            "Linux",
            "Kafka",
        ),
        work=(
            "сценарии нагрузочного тестирования",
            "поиск узких мест и анализ метрик",
            "профилирование систем под нагрузкой",
            "отчёты о производительности для команд",
        ),
        requirements=(
            "опыт нагрузочного тестирования на JMeter или Gatling",
            "умение анализировать метрики в Grafana",
            "понимание архитектуры распределённых систем",
            "базовые навыки программирования",
        ),
        pluses=(
            "опыт с k6",
            "опыт тестирования Kafka",
            "уверенная работа в Linux",
        ),
        fsp=((P, 0.7), (A, 0.3)),
        female_share=0.3,
    ),
    # --- security ---
    Track(
        key="pentest",
        specialization="security",
        titles=("Пентестер", "Специалист по тестированию на проникновение"),
        lead_titles=("Руководитель отдела анализа защищённости",),
        core=("Burp Suite", "Kali Linux"),
        extra=(
            "Nmap",
            "Metasploit",
            "OWASP Top 10",
            "Python",
            "Bash",
            "SQLMap",
            "Wireshark",
            "Active Directory",
            "BloodHound",
            "Hashcat",
            "Nuclei",
        ),
        work=(
            "тестирование на проникновение веб-приложений",
            "анализ защищённости внутренней инфраструктуры и Active Directory",
            "отчёты и рекомендации для заказчиков",
            "red team-проекты",
            "собственные инструменты на Python",
        ),
        requirements=(
            "опыт проведения пентестов веб-приложений",
            "знание OWASP Top 10 и методологий тестирования",
            "опыт работы с Burp Suite",
            "навыки программирования на Python или Bash",
        ),
        pluses=(
            "сертификат OSCP или аналогичный",
            "призовые места в CTF",
            "опыт работы с Active Directory",
        ),
        fsp=((S, 0.85), (A, 0.1), (P, 0.05)),
        female_share=0.15,
        fsp_bonus=0.15,
        domains=("в кибербезопасности", "у интегратора ИБ", "в банковской сфере", "в телекоме"),
    ),
    Track(
        key="appsec",
        specialization="security",
        titles=("AppSec-инженер", "Инженер по безопасной разработке"),
        lead_titles=("Руководитель направления AppSec",),
        core=("OWASP Top 10", "SAST/DAST"),
        extra=(
            "Semgrep",
            "SonarQube",
            "OWASP ZAP",
            "Burp Suite",
            "Python",
            "Go",
            "Docker",
            "Kubernetes",
            "GitLab CI",
            "Trivy",
            "HashiCorp Vault",
            "DefectDojo",
            "Моделирование угроз",
        ),
        work=(
            "внедрение SAST и DAST в CI/CD",
            "моделирование угроз для новых сервисов",
            "ревью кода на уязвимости",
            "обучение разработчиков безопасной разработке",
            "анализ уязвимостей в зависимостях",
        ),
        requirements=(
            "опыт внедрения практик DevSecOps",
            "знание OWASP Top 10 и типовых уязвимостей",
            "опыт работы с SAST/DAST-инструментами",
            "умение читать код на Python, Go или Java",
        ),
        pluses=(
            "опыт моделирования угроз",
            "опыт обеспечения безопасности мобильных приложений",
            "призовые места в CTF",
        ),
        fsp=((S, 0.8), (P, 0.2)),
        female_share=0.2,
        fsp_bonus=0.15,
        domains=("в кибербезопасности", "в финтехе", "в банковской сфере", "в e-commerce"),
    ),
    Track(
        key="soc",
        specialization="security",
        titles=("Аналитик SOC", "Инженер по мониторингу ИБ"),
        lead_titles=("Руководитель SOC",),
        core=("SIEM", "MITRE ATT&CK"),
        extra=(
            "MaxPatrol SIEM",
            "KUMA",
            "ELK",
            "Suricata",
            "Wireshark",
            "Sigma",
            "YARA",
            "Python",
            "EDR",
            "Linux",
            "Windows Event Log",
        ),
        work=(
            "мониторинг и разбор событий ИБ в SIEM",
            "разработка правил корреляции",
            "расследование инцидентов",
            "threat hunting по индикаторам компрометации",
            "взаимодействие с заказчиками по инцидентам",
        ),
        requirements=(
            "понимание сетевых протоколов и устройства ОС",
            "опыт работы с SIEM-системами",
            "знание матрицы MITRE ATT&CK",
            "готовность к сменному графику (для линии L1)",
        ),
        pluses=(
            "опыт написания Sigma-правил",
            "опыт работы с EDR",
            "участие в CTF",
        ),
        fsp=((S, 0.85), (P, 0.15)),
        female_share=0.25,
        fsp_bonus=0.15,
        domains=("в кибербезопасности", "в SOC крупного интегратора", "в госсекторе", "в телекоме"),
    ),
    Track(
        key="reverse",
        specialization="security",
        titles=("Реверс-инженер", "Вирусный аналитик"),
        lead_titles=("Руководитель группы исследования ВПО",),
        core=("IDA Pro", "Ghidra"),
        extra=(
            "Ассемблер x86-64",
            "C",
            "C++",
            "Python",
            "WinDbg",
            "x64dbg",
            "Frida",
            "YARA",
            "Анализ ВПО",
        ),
        work=(
            "анализ вредоносного ПО",
            "реверс-инжиниринг бинарных файлов",
            "YARA-правила и сигнатуры",
            "исследование уязвимостей в ПО",
        ),
        requirements=(
            "опыт реверс-инжиниринга под Windows или Linux",
            "знание ассемблера x86-64",
            "опыт работы с IDA Pro или Ghidra",
            "знание C/C++",
        ),
        pluses=(
            "призовые места в CTF (категория reverse)",
            "опыт анализа мобильных приложений",
            "публикации собственных исследований",
        ),
        fsp=((S, 0.9), (A, 0.1)),
        female_share=0.1,
        fsp_bonus=0.15,
        domains=("в кибербезопасности", "в антивирусной лаборатории", "у интегратора ИБ"),
    ),
    # --- gamedev ---
    Track(
        key="unity",
        specialization="gamedev",
        titles=("Unity-разработчик", "Разработчик игр (Unity)"),
        lead_titles=("Lead Unity-разработчик", "Технический директор игрового проекта"),
        core=("C#", "Unity"),
        extra=(
            "Zenject",
            "UniRx",
            "DOTween",
            "Addressables",
            "Photon",
            "Shader Graph",
            "HLSL",
            "ECS (DOTS)",
            "Firebase",
            "Git LFS",
        ),
        work=(
            "игровые механики на Unity",
            "оптимизация производительности на мобильных устройствах",
            "мультиплеер на Photon",
            "UI и система прогрессии игрока",
            "шейдеры и визуальные эффекты",
        ),
        requirements=(
            "опыт коммерческой разработки на Unity",
            "уверенное знание C#",
            "понимание архитектурных паттернов в геймдеве",
            "опыт оптимизации игр под мобильные устройства",
        ),
        pluses=(
            "опыт с ECS (DOTS)",
            "опыт написания шейдеров",
            "выпущенные проекты в сторах",
        ),
        fsp=((P, 0.8), (A, 0.2)),
        female_share=0.2,
        domains=("в геймдеве", "в мобильных играх", "в инди-студии"),
    ),
    Track(
        key="unreal",
        specialization="gamedev",
        titles=("Unreal Engine-разработчик", "Разработчик игр (Unreal Engine)"),
        lead_titles=("Lead Unreal Engine-разработчик",),
        core=("C++", "Unreal Engine"),
        extra=(
            "Blueprints",
            "Gameplay Ability System",
            "HLSL",
            "Perforce",
            "Сетевой мультиплеер",
            "Niagara",
            "Unreal Insights",
        ),
        work=(
            "игровые системы на C++ в Unreal Engine 5",
            "сетевой мультиплеер",
            "оптимизация производительности и памяти",
            "инструменты для геймдизайнеров",
        ),
        requirements=(
            "опыт разработки на Unreal Engine 4/5",
            "уверенное знание C++",
            "опыт работы с Blueprints",
            "понимание сетевой репликации в Unreal",
        ),
        pluses=(
            "опыт с Gameplay Ability System",
            "выпущенные проекты на PC или консолях",
            "опыт работы с Perforce",
        ),
        fsp=((P, 0.7), (A, 0.3)),
        female_share=0.15,
        domains=("в геймдеве", "в студии PC-игр", "в AAA-проекте"),
    ),
)

TRACKS_BY_KEY: dict[str, Track] = {track.key: track for track in TRACKS}

# How many candidates of each track the dataset has (124 in total).
CANDIDATES_PER_TRACK: dict[str, int] = {
    "python-backend": 8,
    "go-backend": 5,
    "java-backend": 5,
    "kotlin-backend": 2,
    "dotnet-backend": 2,
    "php-backend": 2,
    "node-backend": 2,
    "cpp-backend": 2,
    "rust-backend": 1,
    "react-frontend": 10,
    "vue-frontend": 4,
    "angular-frontend": 2,
    "ts-fullstack": 6,
    "python-fullstack": 3,
    "php-fullstack": 1,
    "ios": 4,
    "android": 5,
    "flutter": 2,
    "react-native": 1,
    "ml-classic": 5,
    "ml-cv": 3,
    "ml-nlp": 3,
    "product-analytics": 3,
    "de-batch": 5,
    "de-stream": 3,
    "devops": 7,
    "sre": 3,
    "qa-manual": 5,
    "qa-auto-python": 3,
    "qa-auto-java": 2,
    "qa-auto-ts": 1,
    "qa-load": 1,
    "pentest": 3,
    "appsec": 2,
    "soc": 2,
    "reverse": 1,
    "unity": 3,
    "unreal": 2,
}

GRADE_SHARES: dict[Grade, float] = {
    Grade.INTERN: 0.09,
    Grade.JUNIOR: 0.24,
    Grade.MIDDLE: 0.36,
    Grade.SENIOR: 0.23,
    Grade.LEAD: 0.08,
}

# Monthly salary in Moscow for the median backend developer of the grade, RUB.
GRADE_SALARY: dict[Grade, int] = {
    Grade.INTERN: 55_000,
    Grade.JUNIOR: 120_000,
    Grade.MIDDLE: 230_000,
    Grade.SENIOR: 360_000,
    Grade.LEAD: 460_000,
}

SPECIALIZATION_SALARY_FACTOR: dict[str, float] = {
    "backend": 1.0,
    "frontend": 0.92,
    "fullstack": 0.97,
    "mobile": 1.0,
    "data-science": 1.07,
    "data-engineering": 1.05,
    "devops": 1.03,
    "qa": 0.78,
    "security": 1.04,
    "gamedev": 0.86,
}

REMOTE_SALARY_FACTOR = 0.95


@dataclass(frozen=True, slots=True)
class City:
    name: str
    locative: str
    # Genitive of the region, for regional FSP events: "Чемпионат Свердловской области …".
    region: str
    weight: int
    salary_factor: float


CITIES: tuple[City, ...] = (
    City("Москва", "в Москве", "Москвы", 30, 1.0),
    City("Санкт-Петербург", "в Санкт-Петербурге", "Санкт-Петербурга", 15, 0.93),
    City("Казань", "в Казани", "Республики Татарстан", 7, 0.85),
    City("Новосибирск", "в Новосибирске", "Новосибирской области", 6, 0.85),
    City("Екатеринбург", "в Екатеринбурге", "Свердловской области", 6, 0.85),
    City("Нижний Новгород", "в Нижнем Новгороде", "Нижегородской области", 5, 0.82),
    City("Иннополис", "в Иннополисе", "Республики Татарстан", 2, 0.9),
    City("Томск", "в Томске", "Томской области", 3, 0.8),
    City("Самара", "в Самаре", "Самарской области", 3, 0.78),
    City("Краснодар", "в Краснодаре", "Краснодарского края", 3, 0.8),
    City("Ростов-на-Дону", "в Ростове-на-Дону", "Ростовской области", 3, 0.8),
    City("Пермь", "в Перми", "Пермского края", 2, 0.78),
    City("Воронеж", "в Воронеже", "Воронежской области", 2, 0.76),
    City("Уфа", "в Уфе", "Республики Башкортостан", 2, 0.78),
    City("Калининград", "в Калининграде", "Калининградской области", 2, 0.8),
    City("Владивосток", "во Владивостоке", "Приморского края", 2, 0.85),
    City("Тюмень", "в Тюмени", "Тюменской области", 2, 0.82),
    City("Ярославль", "в Ярославле", "Ярославской области", 2, 0.76),
    City("Челябинск", "в Челябинске", "Челябинской области", 2, 0.76),
)

CITIES_BY_NAME: dict[str, City] = {city.name: city for city in CITIES}


@dataclass(frozen=True, slots=True)
class University:
    # Genitive, as in "студент 3-го курса <name>".
    name: str
    city: str
    majors: tuple[str, ...]


UNIVERSITIES: tuple[University, ...] = (
    University("МФТИ", "Москва", ("Прикладная математика и физика",)),
    University(
        "НИУ ВШЭ", "Москва", ("Прикладная математика и информатика", "Программная инженерия")
    ),
    University(
        "МГТУ им. Н. Э. Баумана",
        "Москва",
        ("Информатика и вычислительная техника", "Программная инженерия"),
    ),
    University("МГУ им. М. В. Ломоносова", "Москва", ("Прикладная математика и информатика",)),
    University("НИЯУ МИФИ", "Москва", ("Информационная безопасность", "Прикладная информатика")),
    University(
        "ИТМО",
        "Санкт-Петербург",
        ("Программная инженерия", "Информационная безопасность", "Прикладная информатика"),
    ),
    University(
        "СПбГУ",
        "Санкт-Петербург",
        ("Математическое обеспечение и администрирование информационных систем",),
    ),
    University(
        "СПбПУ Петра Великого",
        "Санкт-Петербург",
        ("Информатика и вычислительная техника", "Информационная безопасность"),
    ),
    University(
        "КФУ",
        "Казань",
        ("Программная инженерия", "Фундаментальная информатика и информационные технологии"),
    ),
    University("Университета Иннополис", "Иннополис", ("Программная инженерия", "Науки о данных")),
    University("НГУ", "Новосибирск", ("Математика и компьютерные науки",)),
    University("НГТУ", "Новосибирск", ("Программная инженерия",)),
    University("УрФУ", "Екатеринбург", ("Программная инженерия", "Прикладная информатика")),
    University("ТПУ", "Томск", ("Информатика и вычислительная техника",)),
    University("ТУСУР", "Томск", ("Информационная безопасность", "Программная инженерия")),
    University(
        "ННГУ им. Н. И. Лобачевского",
        "Нижний Новгород",
        ("Фундаментальная информатика и информационные технологии",),
    ),
    University("Самарского университета", "Самара", ("Прикладная информатика",)),
    University("КубГУ", "Краснодар", ("Прикладная информатика",)),
    University("ЮФУ", "Ростов-на-Дону", ("Прикладная информатика", "Информационная безопасность")),
    University("ПНИПУ", "Пермь", ("Программная инженерия",)),
    University("ВГУ", "Воронеж", ("Прикладная математика и информатика",)),
    University("УУНиТ", "Уфа", ("Прикладная информатика",)),
    University("БФУ им. И. Канта", "Калининград", ("Прикладная математика и информатика",)),
    University("ДВФУ", "Владивосток", ("Программная инженерия",)),
    University("ТюмГУ", "Тюмень", ("Информационная безопасность",)),
    University("ЯрГУ им. П. Г. Демидова", "Ярославль", ("Прикладная математика и информатика",)),
    University("ЮУрГУ", "Челябинск", ("Программная инженерия",)),
)

MALE_NAMES: tuple[str, ...] = (
    "Александр",
    "Алексей",
    "Андрей",
    "Антон",
    "Арсений",
    "Артём",
    "Айдар",
    "Богдан",
    "Вадим",
    "Виктор",
    "Владимир",
    "Владислав",
    "Георгий",
    "Глеб",
    "Григорий",
    "Даниил",
    "Денис",
    "Дмитрий",
    "Евгений",
    "Егор",
    "Иван",
    "Игорь",
    "Илья",
    "Кирилл",
    "Константин",
    "Лев",
    "Максим",
    "Марат",
    "Марк",
    "Матвей",
    "Михаил",
    "Никита",
    "Николай",
    "Олег",
    "Павел",
    "Ринат",
    "Роман",
    "Руслан",
    "Семён",
    "Сергей",
    "Степан",
    "Тимофей",
    "Тимур",
    "Фёдор",
    "Ярослав",
)

FEMALE_NAMES: tuple[str, ...] = (
    "Александра",
    "Алина",
    "Алиса",
    "Алсу",
    "Анастасия",
    "Анна",
    "Арина",
    "Валерия",
    "Варвара",
    "Вера",
    "Вероника",
    "Виктория",
    "Дарья",
    "Диана",
    "Динара",
    "Ева",
    "Екатерина",
    "Елена",
    "Елизавета",
    "Ирина",
    "Камила",
    "Карина",
    "Кристина",
    "Ксения",
    "Лилия",
    "Мария",
    "Марина",
    "Милана",
    "Надежда",
    "Наталья",
    "Олеся",
    "Полина",
    "Регина",
    "Светлана",
    "Софья",
    "Таисия",
    "Ульяна",
    "Эльвира",
    "Юлия",
    "Яна",
)

# Masculine forms; the feminine form is derived (Иванов → Иванова, Островский → Островская).
SURNAMES: tuple[str, ...] = (
    "Абрамов",
    "Алексеев",
    "Андреев",
    "Антонов",
    "Афанасьев",
    "Ахметов",
    "Баранов",
    "Белов",
    "Беляев",
    "Богданов",
    "Бондаренко",
    "Борисов",
    "Быков",
    "Валиев",
    "Васильев",
    "Виноградов",
    "Вишневский",
    "Власов",
    "Волков",
    "Воробьёв",
    "Гаврилов",
    "Галиев",
    "Гарипов",
    "Герасимов",
    "Голубев",
    "Горбунов",
    "Григорьев",
    "Гусев",
    "Давыдов",
    "Данилов",
    "Денисов",
    "Дмитриев",
    "Егоров",
    "Ефимов",
    "Жуков",
    "Зайцев",
    "Захаров",
    "Зуев",
    "Иванов",
    "Ильин",
    "Исаев",
    "Казаков",
    "Калинин",
    "Карпов",
    "Ким",
    "Киселёв",
    "Ковалёв",
    "Козлов",
    "Колесников",
    "Комаров",
    "Кондратьев",
    "Королёв",
    "Крылов",
    "Кудрявцев",
    "Кузнецов",
    "Кузьмин",
    "Куликов",
    "Лазарев",
    "Лебедев",
    "Макаров",
    "Максимов",
    "Марков",
    "Матвеев",
    "Медведев",
    "Мельников",
    "Миронов",
    "Михайлов",
    "Морозов",
    "Мухаметов",
    "Назаров",
    "Никитин",
    "Николаев",
    "Новиков",
    "Орлов",
    "Осипов",
    "Островский",
    "Павлов",
    "Петров",
    "Покровский",
    "Поляков",
    "Пономарёв",
    "Попов",
    "Романов",
    "Савченко",
    "Сафин",
    "Свиридов",
    "Семёнов",
    "Сергеев",
    "Сидоров",
    "Смирнов",
    "Соболев",
    "Соколов",
    "Соловьёв",
    "Сорокин",
    "Степанов",
    "Тарасов",
    "Тимофеев",
    "Титов",
    "Тихонов",
    "Ткаченко",
    "Федотов",
    "Филиппов",
    "Фомин",
    "Фролов",
    "Фёдоров",
    "Хабибуллин",
    "Цой",
    "Чернов",
    "Шарипов",
    "Шевченко",
    "Щербаков",
    "Юдин",
    "Яковлев",
)

# Prepositional phrases: "3 года в IT, из них 2 — <domain>".
DOMAINS: tuple[str, ...] = (
    "в финтехе",
    "в e-commerce",
    "в логистике",
    "в медтехе",
    "в EdTech",
    "в телекоме",
    "в госсекторе",
    "в ритейле",
    "в банковской сфере",
    "в маркетплейсе",
    "в стриминговом сервисе",
    "в промышленной автоматизации",
    "в агротехе",
    "в travel-tech",
    "в foodtech",
    "в заказной разработке",
    "в продуктовой студии",
)

SOFT_SKILLS: tuple[str, ...] = (
    "Коммуникабельность",
    "Работа в команде",
    "Ответственность",
    "Самоорганизация",
    "Критическое мышление",
    "Обучаемость",
    "Внимание к деталям",
    "Публичные выступления",
    "Управление временем",
    "Адаптивность",
    "Системное мышление",
    "Ведение переговоров",
    "Эмпатия",
)

LEADERSHIP_SKILLS: tuple[str, ...] = ("Наставничество", "Лидерство")

ENGLISH_LEVELS: dict[Grade, tuple[tuple[str, int], ...]] = {
    Grade.INTERN: (("A2", 2), ("B1", 4), ("B2", 3), ("C1", 1)),
    Grade.JUNIOR: (("A2", 2), ("B1", 4), ("B2", 3), ("C1", 1)),
    Grade.MIDDLE: (("A2", 1), ("B1", 3), ("B2", 4), ("C1", 2)),
    Grade.SENIOR: (("B1", 3), ("B2", 4), ("C1", 2), ("C2", 1)),
    Grade.LEAD: (("B1", 2), ("B2", 4), ("C1", 3), ("C2", 1)),
}

OFC = WorkFormat.OFFICE
HYB = WorkFormat.HYBRID
RMT = WorkFormat.REMOTE

# Acceptable work formats of a candidate and their weights.
WORK_FORMAT_PATTERNS: tuple[tuple[tuple[WorkFormat, ...], int], ...] = (
    ((RMT,), 30),
    ((RMT, HYB), 30),
    ((HYB, OFC), 15),
    ((OFC, HYB, RMT), 15),
    ((OFC,), 5),
    ((HYB,), 5),
)

INTERN_WORK_FORMAT_PATTERNS: tuple[tuple[tuple[WorkFormat, ...], int], ...] = (
    ((RMT,), 10),
    ((RMT, HYB), 20),
    ((HYB, OFC), 30),
    ((OFC, HYB, RMT), 25),
    ((OFC,), 10),
    ((HYB,), 5),
)

SENIOR_LINES: tuple[str, ...] = (
    "Менторю младших коллег и провожу технические собеседования.",
    "Отвечаю за ключевые технические решения в своём направлении.",
    "Довожу сложные задачи от идеи до продакшена.",
    "Выстраиваю процессы и делюсь опытом на внутренних митапах.",
)

LEAD_LINES: tuple[str, ...] = (
    "Отвечаю за найм, развитие людей и качество поставки.",
    "Совмещаю управление командой с технической экспертизой и код-ревью.",
    "Выстраиваю процессы, ставлю цели команде и защищаю roadmap перед бизнесом.",
)

CLOSING_LINES: tuple[str, ...] = (
    "Ценю прозрачные процессы и понятные цели.",
    "Люблю сложные задачи и сильные команды.",
    "Интересны продукты, которые приносят пользу людям.",
    "Ищу команду с сильной инженерной культурой.",
)

FSP_DISCIPLINE_LABELS: dict[FspDiscipline, str] = {
    A: "алгоритмическое программирование",
    P: "продуктовое программирование",
    S: "программирование систем информационной безопасности",
    R: "программирование робототехники",
    U: "программирование беспилотных авиационных систем",
}

FSP_DISCIPLINE_DATIVE: dict[FspDiscipline, str] = {
    A: "алгоритмическому программированию",
    P: "продуктовому программированию",
    S: "программированию систем информационной безопасности",
    R: "программированию робототехники",
    U: "программированию беспилотных авиационных систем",
}

FSP_NATIONAL_EVENTS: tuple[str, ...] = (
    "Чемпионат России по спортивному программированию",
    "Кубок России по спортивному программированию",
    "Всероссийские соревнования по спортивному программированию",
)

FSP_YOUTH_EVENT = "Первенство России по спортивному программированию"

FSP_REGIONAL_EVENTS: tuple[str, ...] = (
    "Чемпионат {region} по спортивному программированию",
    "Кубок {region} по спортивному программированию",
)

# Probability that a candidate of the grade has linked an FSP ID (before the track bonus).
FSP_LINK_SHARE: dict[Grade, float] = {
    Grade.INTERN: 0.75,
    Grade.JUNIOR: 0.6,
    Grade.MIDDLE: 0.45,
    Grade.SENIOR: 0.3,
    Grade.LEAD: 0.2,
}

# --- vacancies -----------------------------------------------------------------------------------

EXPERIENCE_REQUIREMENTS: dict[Grade, str] = {
    Grade.INTERN: "обучение на старших курсах или недавний выпуск по профильному направлению",
    Grade.JUNIOR: "опыт от полугода, включая стажировки и пет-проекты",
    Grade.MIDDLE: "коммерческий опыт от 2 лет",
    Grade.SENIOR: "коммерческий опыт от 4 лет",
    Grade.LEAD: "опыт от 6 лет, из них не менее года — в роли тимлида",
}

# Followed by tool names in the instrumental case, which Latin names don't need.
STACK_REQUIREMENT_PREFIX: dict[Grade, str] = {
    Grade.INTERN: "знакомство с",
    Grade.JUNIOR: "опыт работы с",
    Grade.MIDDLE: "опыт работы с",
    Grade.SENIOR: "уверенный опыт работы с",
    Grade.LEAD: "уверенный опыт работы с",
}

FSP_PLUS = "участие в соревнованиях ФСП или хакатонах"

FORMAT_CONDITIONS: dict[WorkFormat, str] = {
    WorkFormat.REMOTE: "удалённая работа из любого города России",
    WorkFormat.HYBRID: "гибридный формат: 2–3 дня в неделю в офисе {city}",
    WorkFormat.OFFICE: "работа в офисе {city}",
}

GRADE_CONDITIONS: dict[Grade, str] = {
    Grade.INTERN: "оплачиваемая стажировка на 3–6 месяцев с возможностью перехода в штат",
    Grade.JUNIOR: "наставник на время адаптации и план развития на полгода",
    Grade.SENIOR: "годовой бонус по результатам работы",
    Grade.LEAD: "годовой бонус и участие в опционной программе",
}

CONDITIONS: tuple[str, ...] = (
    "официальное оформление в аккредитованной IT-компании",
    "ДМС со стоматологией после испытательного срока",
    "компенсация обучения, конференций и профессиональной литературы",
    "техника на выбор: MacBook или ноутбук с Linux",
    "гибкое начало рабочего дня",
    "пересмотр дохода дважды в год по прозрачной системе грейдов",
    "внутренние митапы, хакатоны и гильдии",
    "компенсация занятий спортом",
)


@dataclass(frozen=True, slots=True)
class VacancyPlan:
    track: str
    grade: Grade
    title: str
    work_format: WorkFormat
    # What the team does; opens the description.
    team: str
    # None = draft (not published yet).
    published_days_ago: int | None
    # Technologies the title promises; always included in the stack.
    stack: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class CompanyPlan:
    key: str
    name: str
    industry: str
    city: str
    size: str
    description: str
    vacancies: tuple[VacancyPlan, ...]


INT = Grade.INTERN
JUN = Grade.JUNIOR
MID = Grade.MIDDLE
SEN = Grade.SENIOR
LEAD = Grade.LEAD

COMPANIES: tuple[CompanyPlan, ...] = (
    CompanyPlan(
        key="payflow",
        name="ПэйФлоу",
        industry="Финтех: платёжные сервисы",
        city="Москва",
        size="501–1000",
        description=(
            "Платёжная платформа для онлайн-бизнеса: интернет-эквайринг, СБП, выплаты "
            "самозанятым и антифрод. Через нас проходит более 3 млн транзакций в сутки, а "
            "платёжный шлюз работает с доступностью 99,99%."
        ),
        vacancies=(
            VacancyPlan(
                "java-backend",
                SEN,
                "Senior Java-разработчик (процессинг платежей)",
                HYB,
                "Команда процессинга проводит платежи по картам и СБП: 3 млн транзакций в сутки "
                "и SLA 99,99%.",
                2,
                ("Kafka", "PostgreSQL"),
            ),
            VacancyPlan(
                "go-backend",
                MID,
                "Go-разработчик в команду антифрода",
                RMT,
                "Антифрод проверяет каждую транзакцию за 50 мс и блокирует мошеннические операции "
                "до списания денег.",
                5,
                ("Kafka", "ClickHouse"),
            ),
            VacancyPlan(
                "go-backend",
                LEAD,
                "Тимлид команды антифрода (Go)",
                HYB,
                "Ищем руководителя команды из 6 разработчиков: правила и ML-скоринг транзакций "
                "в реальном времени.",
                12,
                ("Kafka",),
            ),
            VacancyPlan(
                "react-frontend",
                MID,
                "Frontend-разработчик (личный кабинет мерчанта)",
                HYB,
                "В личном кабинете 40 000 магазинов смотрят платежи, возвраты и аналитику.",
                8,
            ),
            VacancyPlan(
                "qa-auto-java",
                JUN,
                "Junior QA Automation-инженер (Java)",
                HYB,
                "В QA-гильдии 12 человек; новичков ведёт наставник, а автотесты запускаются на "
                "каждый merge request.",
                20,
            ),
            VacancyPlan(
                "sre",
                SEN,
                "SRE-инженер (платёжный шлюз)",
                HYB,
                "Отвечаем за надёжность платёжного шлюза: 20 сервисов, 3 дата-центра и нулевая "
                "терпимость к простоям.",
                15,
            ),
        ),
    ),
    CompanyPlan(
        key="severny-kod",
        name="Северный код",
        industry="Заказная разработка ПО",
        city="Санкт-Петербург",
        size="201–500",
        description=(
            "Разрабатываем веб- и мобильные продукты для ритейла, банков и медицины: более 120 "
            "проектов за 12 лет. Своя школа стажёров, прозрачные грейды и наставник у каждого "
            "новичка."
        ),
        vacancies=(
            VacancyPlan(
                "python-backend",
                JUN,
                "Junior Python-разработчик",
                HYB,
                "Проектная команда делает сервисы для ритейла и логистики; у каждого джуниора "
                "есть ментор и индивидуальный план развития.",
                3,
                ("Django",),
            ),
            VacancyPlan(
                "python-backend",
                INT,
                "Стажёр Python-разработчик",
                OFC,
                "Оплачиваемая стажировка в школе «Северного кода»: три месяца реальных задач и "
                "оффер лучшим стажёрам.",
                6,
            ),
            VacancyPlan(
                "flutter",
                MID,
                "Flutter-разработчик",
                RMT,
                "Делаем мобильные приложения для ритейла и HoReCa — от MVP до приложений с "
                "миллионом установок.",
                9,
            ),
            VacancyPlan(
                "qa-manual",
                INT,
                "Стажёр-тестировщик",
                OFC,
                "Учим тестированию с нуля на реальных проектах; после стажировки — переход в штат.",
                4,
            ),
            VacancyPlan(
                "vue-frontend",
                MID,
                "Frontend-разработчик (Vue 3)",
                HYB,
                "Команда делает B2B-порталы и личные кабинеты для банков и страховых компаний.",
                11,
            ),
            VacancyPlan(
                "php-fullstack",
                MID,
                "Fullstack-разработчик (PHP + Vue)",
                RMT,
                "Поддерживаем и развиваем CRM для сети медицинских клиник.",
                18,
            ),
            VacancyPlan(
                "qa-manual",
                LEAD,
                "Руководитель отдела тестирования",
                HYB,
                "В отделе 25 тестировщиков на 15 проектах; нужно выстроить единые стандарты "
                "качества и развивать автоматизацию.",
                25,
            ),
        ),
    ),
    CompanyPlan(
        key="graviton-games",
        name="Гравитон Геймс",
        industry="Разработка игр",
        city="Казань",
        size="51–200",
        description=(
            "Независимая игровая студия: мобильная RPG с 5 млн загрузок и кооперативный экшен на "
            "Unreal Engine 5 в разработке. Ценим геймплей, честную монетизацию и плейтесты по "
            "пятницам."
        ),
        vacancies=(
            VacancyPlan(
                "unity",
                MID,
                "Unity-разработчик (мобильная RPG)",
                HYB,
                "Развиваем мобильную RPG с 5 млн загрузок: новые сезоны, PvP-режимы и ивенты "
                "каждые две недели.",
                4,
            ),
            VacancyPlan(
                "unreal",
                SEN,
                "Senior Unreal Engine-разработчик (C++)",
                RMT,
                "Делаем кооперативный экшен на Unreal Engine 5 для PC и консолей; в команде "
                "35 человек.",
                10,
                ("Сетевой мультиплеер",),
            ),
            VacancyPlan(
                "unity",
                INT,
                "Стажёр Unity-разработчик",
                OFC,
                "Стажировка в игровой студии: прототипы механик под руководством ведущих "
                "разработчиков.",
                7,
            ),
            VacancyPlan(
                "qa-manual",
                JUN,
                "QA-инженер (игровое тестирование)",
                HYB,
                "Тестируем игровые механики, баланс и сетевые режимы перед каждым обновлением.",
                14,
                ("Мобильное тестирование",),
            ),
            VacancyPlan(
                "unity",
                LEAD,
                "Lead Unity-разработчик",
                HYB,
                "Нужен технический лидер нового мобильного проекта: архитектура клиента, найм и "
                "развитие команды из 5 человек.",
                21,
            ),
        ),
    ),
    CompanyPlan(
        key="medintellect",
        name="МедИнтеллект",
        industry="Медтех: ИИ-диагностика",
        city="Москва",
        size="51–200",
        description=(
            "Создаём системы компьютерного зрения, которые помогают врачам находить патологии на "
            "КТ, МРТ и рентгеновских снимках. Наши решения зарегистрированы как медицинские "
            "изделия и работают в 40+ клиниках."
        ),
        vacancies=(
            VacancyPlan(
                "ml-cv",
                SEN,
                "Senior ML-инженер (Computer Vision)",
                HYB,
                "Обучаем модели поиска патологий на КТ и рентгеновских снимках; качество моделей "
                "подтверждено клиническими испытаниями.",
                3,
            ),
            VacancyPlan(
                "python-backend",
                MID,
                "Python-разработчик (платформа инференса)",
                RMT,
                "Платформа принимает снимки из 40 клиник, ставит задачи моделям и возвращает "
                "врачам результаты за минуты.",
                6,
                ("FastAPI", "RabbitMQ"),
            ),
            VacancyPlan(
                "de-batch",
                MID,
                "Data Engineer (медицинские данные)",
                HYB,
                "Строим хранилище обезличенных медицинских данных для обучения моделей.",
                16,
            ),
            VacancyPlan(
                "react-frontend",
                JUN,
                "Junior Frontend-разработчик (DICOM-вьюер)",
                HYB,
                "Разрабатываем веб-просмотрщик медицинских снимков, которым врачи пользуются "
                "каждый день.",
                9,
            ),
        ),
    ),
    CompanyPlan(
        key="kibershield",
        name="КиберЩит",
        industry="Информационная безопасность",
        city="Москва",
        size="201–500",
        description=(
            "Сервисный провайдер кибербезопасности: круглосуточный SOC, пентесты и безопасная "
            "разработка. Защищаем более 150 компаний из финансового сектора, промышленности и "
            "госсектора."
        ),
        vacancies=(
            VacancyPlan(
                "pentest",
                MID,
                "Пентестер (внешний и внутренний периметр)",
                HYB,
                "Команда анализа защищённости проводит больше 80 пентестов в год для банков и "
                "промышленности.",
                2,
                ("Active Directory",),
            ),
            VacancyPlan(
                "soc",
                JUN,
                "Аналитик SOC (L1)",
                OFC,
                "Круглосуточный SOC следит за инфраструктурой 150 заказчиков; график 2/2, "
                "обучение за счёт компании.",
                5,
            ),
            VacancyPlan(
                "appsec",
                SEN,
                "AppSec-инженер",
                RMT,
                "Помогаем заказчикам встроить безопасность в разработку: от моделирования угроз "
                "до DevSecOps-конвейера.",
                13,
            ),
            VacancyPlan(
                "reverse",
                SEN,
                "Вирусный аналитик",
                OFC,
                "Исследуем вредоносное ПО, которое атакует российские компании, и пишем детекты "
                "для наших продуктов.",
                19,
            ),
            VacancyPlan(
                "go-backend",
                MID,
                "Go-разработчик (платформа SIEM)",
                HYB,
                "Разрабатываем собственную SIEM-платформу: сбор, нормализация и корреляция "
                "миллиардов событий в сутки.",
                8,
                ("ClickHouse", "Kafka"),
            ),
        ),
    ),
    CompanyPlan(
        key="gruztech",
        name="ГрузТех",
        industry="Логистика и грузоперевозки",
        city="Екатеринбург",
        size="501–1000",
        description=(
            "Цифровая платформа грузоперевозок: биржа заказов, маршрутизация и приложение для "
            "водителей. Через платформу ежедневно проходит 12 000 рейсов по всей России."
        ),
        vacancies=(
            VacancyPlan(
                "kotlin-backend",
                SEN,
                "Senior Kotlin-разработчик (маршрутизация)",
                HYB,
                "Сервис маршрутизации строит оптимальные рейсы для 30 000 грузовиков по всей "
                "стране.",
                4,
            ),
            VacancyPlan(
                "android",
                MID,
                "Android-разработчик (приложение водителя)",
                RMT,
                "Приложение водителя работает в дороге без интернета: заказы, навигация и "
                "электронные документы.",
                7,
            ),
            VacancyPlan(
                "ml-classic",
                MID,
                "Data Scientist (прогноз спроса и времени доставки)",
                HYB,
                "Прогнозируем спрос на перевозки и время прибытия грузов; модели влияют на цены "
                "и загрузку парка.",
                12,
            ),
            VacancyPlan(
                "devops",
                MID,
                "DevOps-инженер",
                HYB,
                "Инфраструктура — 200 сервисов в Kubernetes в двух облаках; переходим на GitOps.",
                17,
                ("Argo CD",),
            ),
            VacancyPlan(
                "product-analytics",
                INT,
                "Стажёр-аналитик данных",
                OFC,
                "Стажировка в команде аналитики: SQL, дашборды и первые исследования под "
                "руководством ментора.",
                10,
            ),
        ),
    ),
    CompanyPlan(
        key="edusphere",
        name="ЭдуСфера",
        industry="EdTech: онлайн-образование",
        city="Новосибирск",
        size="201–500",
        description=(
            "Онлайн-платформа для школ и вузов: интерактивные курсы, автоматическая проверка "
            "заданий и аналитика успеваемости. Нашими курсами пользуются 2 млн учеников в 70 "
            "регионах."
        ),
        vacancies=(
            VacancyPlan(
                "node-backend",
                MID,
                "Node.js-разработчик (платформа курсов)",
                RMT,
                "Платформой пользуются 2 млн школьников и студентов; команда ведёт ядро курсов и "
                "автопроверку заданий.",
                5,
            ),
            VacancyPlan(
                "react-frontend",
                SEN,
                "Senior Frontend-разработчик (React)",
                RMT,
                "Отвечаем за интерактивный редактор уроков и тренажёры по программированию.",
                9,
            ),
            VacancyPlan(
                "product-analytics",
                JUN,
                "Junior аналитик данных",
                HYB,
                "Изучаем, как ученики проходят курсы, и помогаем методистам делать обучение "
                "эффективнее.",
                15,
            ),
            VacancyPlan(
                "qa-auto-ts",
                MID,
                "QA Automation-инженер (TypeScript, Playwright)",
                RMT,
                "Строим автотесты веб-платформы с нуля; сейчас e2e-тесты покрывают около 30% "
                "сценариев.",
                22,
            ),
            VacancyPlan(
                "python-fullstack",
                JUN,
                "Junior Fullstack-разработчик (Python + React)",
                HYB,
                "Команда внутренних сервисов делает инструменты для методистов и службы поддержки.",
                11,
            ),
            VacancyPlan(
                "react-frontend",
                INT,
                "Стажёр Frontend-разработчик",
                HYB,
                "Стажировка в команде интерфейсов: вёрстка, компоненты на React и код-ревью от "
                "опытных коллег.",
                13,
            ),
        ),
    ),
    CompanyPlan(
        key="onega-bank",
        name="Онега Банк",
        industry="Банковские технологии",
        city="Москва",
        size="5000+",
        description=(
            "Цифровой банк для частных клиентов и малого бизнеса. В собственном IT больше 2 000 "
            "инженеров, а мобильный банк обновляется каждые две недели."
        ),
        vacancies=(
            VacancyPlan(
                "java-backend",
                MID,
                "Java-разработчик (кредитный конвейер)",
                HYB,
                "Кредитный конвейер принимает решение по заявке за 2 минуты; автоматизируем "
                "скоринг и выдачу.",
                3,
                ("Camunda",),
            ),
            VacancyPlan(
                "ios",
                SEN,
                "Senior iOS-разработчик (мобильный банк)",
                HYB,
                "У мобильного банка 4 млн активных пользователей и релизы каждые две недели.",
                6,
                ("SwiftUI",),
            ),
            VacancyPlan(
                "android",
                SEN,
                "Senior Android-разработчик (мобильный банк)",
                HYB,
                "Развиваем мобильный банк для Android: платежи, инвестиции и кешбэк-сервисы.",
                6,
                ("Jetpack Compose",),
            ),
            VacancyPlan(
                "ios",
                LEAD,
                "Руководитель мобильной разработки",
                HYB,
                "Нужен руководитель четырёх мобильных команд (iOS и Android): архитектура, "
                "процесс релизов и развитие людей.",
                24,
            ),
            VacancyPlan(
                "de-batch",
                SEN,
                "Senior Data Engineer (DWH)",
                HYB,
                "Корпоративное хранилище на Greenplum и ClickHouse — источник данных для 300 "
                "аналитиков банка.",
                10,
                ("Greenplum", "ClickHouse"),
            ),
            VacancyPlan(
                "qa-load",
                MID,
                "Инженер по нагрузочному тестированию",
                HYB,
                "Проверяем, что банк выдерживает пиковые нагрузки в дни зарплат и распродаж.",
                14,
            ),
            VacancyPlan(
                "dotnet-backend",
                MID,
                "C#-разработчик (интеграции с АБС)",
                OFC,
                "Связываем автоматизированную банковскую систему с цифровыми каналами.",
                None,
            ),
        ),
    ),
    CompanyPlan(
        key="korzinka",
        name="Корзинка",
        industry="E-commerce: маркетплейс",
        city="Москва",
        size="1001–5000",
        description=(
            "Маркетплейс товаров для дома и повседневных покупок с доставкой за 2 часа в 30 "
            "городах. Каждый месяц у нас покупают 12 млн человек."
        ),
        vacancies=(
            VacancyPlan(
                "go-backend",
                SEN,
                "Senior Go-разработчик (каталог и поиск)",
                RMT,
                "Каталог из 3 млн товаров и поиск, которым пользуются 12 млн покупателей в месяц.",
                2,
                ("Elasticsearch",),
            ),
            VacancyPlan(
                "react-frontend",
                MID,
                "Frontend-разработчик (витрина маркетплейса)",
                RMT,
                "Витрина — главная точка входа покупателей; каждое изменение проверяем A/B-тестом.",
                4,
                ("Next.js",),
            ),
            VacancyPlan(
                "ml-classic",
                SEN,
                "Senior Data Scientist (рекомендательные системы)",
                HYB,
                "Рекомендации приносят 30% выручки маркетплейса; развиваем персонализацию "
                "главной страницы и корзины.",
                8,
            ),
            VacancyPlan(
                "ml-classic",
                LEAD,
                "Lead Data Scientist",
                HYB,
                "Ищем лидера объединённой команды ценообразования и рекомендаций — 8 "
                "DS-специалистов.",
                20,
            ),
            VacancyPlan(
                "react-native",
                MID,
                "React Native-разработчик",
                RMT,
                "Мобильное приложение маркетплейса на React Native: через него приходит 60% "
                "заказов.",
                7,
            ),
            VacancyPlan(
                "product-analytics",
                MID,
                "Продуктовый аналитик",
                HYB,
                "Помогаем командам принимать решения на данных: метрики, эксперименты и "
                "исследования поведения покупателей.",
                12,
                ("ClickHouse",),
            ),
        ),
    ),
    CompanyPlan(
        key="televolna",
        name="ТелеВолна",
        industry="Телекоммуникации",
        city="Нижний Новгород",
        size="1001–5000",
        description=(
            "Федеральный оператор связи: мобильная связь, домашний интернет и IoT-решения для "
            "бизнеса. Собственная разработка биллинга, CRM и систем мониторинга сети."
        ),
        vacancies=(
            VacancyPlan(
                "java-backend",
                JUN,
                "Junior Java-разработчик (биллинг)",
                HYB,
                "Биллинг считает услуги 20 млн абонентов; новичкам даём наставника и понятный "
                "план адаптации.",
                6,
            ),
            VacancyPlan(
                "devops",
                SEN,
                "Senior DevOps-инженер (частное облако)",
                HYB,
                "Строим частное облако на OpenStack и Kubernetes для внутренних команд и "
                "B2B-клиентов.",
                11,
            ),
            VacancyPlan(
                "qa-manual",
                MID,
                "QA-инженер (биллинг и CRM)",
                OFC,
                "Тестируем тарифы, начисления и CRM для операторов контакт-центра.",
                16,
            ),
            VacancyPlan(
                "cpp-backend",
                MID,
                "C++-разработчик (сетевое оборудование)",
                OFC,
                "Разрабатываем ПО для собственного сетевого оборудования и систем мониторинга "
                "сети.",
                None,
            ),
        ),
    ),
    CompanyPlan(
        key="aerovector",
        name="АэроВектор",
        industry="Беспилотные авиационные системы",
        city="Иннополис",
        size="51–200",
        description=(
            "Проектируем беспилотники для агромониторинга и инспекции ЛЭП — от бортового ПО до "
            "облачной платформы обработки аэроснимков. Резидент особой экономической зоны "
            "«Иннополис»."
        ),
        vacancies=(
            VacancyPlan(
                "cpp-backend",
                SEN,
                "Senior C++-разработчик (бортовое ПО)",
                OFC,
                "Пишем бортовое ПО для БПЛА: навигация, стабилизация полёта и автономные миссии.",
                5,
                ("ROS 2",),
            ),
            VacancyPlan(
                "ml-cv",
                MID,
                "ML-инженер (детекция объектов на аэроснимках)",
                HYB,
                "Модели находят повреждения ЛЭП и очаги болезней растений на снимках с дронов.",
                9,
                ("YOLO",),
            ),
            VacancyPlan(
                "python-backend",
                MID,
                "Python-разработчик (облачная платформа)",
                RMT,
                "Облачная платформа принимает гигабайты снимков с дронов и строит по ним "
                "ортофотопланы.",
                13,
            ),
            VacancyPlan(
                "cpp-backend",
                INT,
                "Стажёр C++-разработчик (симуляция полёта)",
                OFC,
                "Стажировка в команде симуляции: моделирование полёта и проверка алгоритмов на "
                "стенде.",
                8,
            ),
        ),
    ),
    CompanyPlan(
        key="digital-region",
        name="Цифровой регион",
        industry="GovTech: цифровые госуслуги",
        city="Казань",
        size="201–500",
        description=(
            "Создаём цифровые сервисы для жителей и органов власти региона: портал услуг, "
            "запись к врачу, электронные очереди и аналитические панели."
        ),
        vacancies=(
            VacancyPlan(
                "python-backend",
                MID,
                "Python-разработчик (региональный портал услуг)",
                HYB,
                "Портал услуг региона: запись к врачу, детские сады, транспорт — 1,5 млн "
                "пользователей.",
                4,
                ("Django",),
            ),
            VacancyPlan(
                "angular-frontend",
                MID,
                "Frontend-разработчик (Angular)",
                HYB,
                "Делаем интерфейсы ведомственных систем, с которыми ежедневно работают 8 000 "
                "сотрудников.",
                10,
            ),
            VacancyPlan(
                "soc",
                MID,
                "Инженер по информационной безопасности (SOC)",
                OFC,
                "Защищаем государственные информационные системы региона и реагируем на инциденты.",
                15,
            ),
            VacancyPlan(
                "qa-manual",
                JUN,
                "Junior QA-инженер",
                OFC,
                "Тестируем государственные сервисы перед запуском; обучение и наставник с "
                "первого дня.",
                19,
            ),
        ),
    ),
    CompanyPlan(
        key="agrodata",
        name="АгроДата",
        industry="AgroTech",
        city="Краснодар",
        size="51–200",
        description=(
            "Платформа точного земледелия: спутниковый мониторинг полей, прогноз урожайности и "
            "учёт техники. Нашими сервисами пользуются агрохолдинги с 2 млн гектаров полей."
        ),
        vacancies=(
            VacancyPlan(
                "ml-classic",
                MID,
                "Data Scientist (прогноз урожайности)",
                RMT,
                "Прогнозируем урожайность по спутниковым снимкам и данным метеостанций для "
                "2 млн гектаров полей.",
                6,
            ),
            VacancyPlan(
                "ts-fullstack",
                MID,
                "Fullstack-разработчик (TypeScript)",
                RMT,
                "Небольшая продуктовая команда: карта полей, учёт техники и рабочее место "
                "агронома.",
                12,
            ),
            VacancyPlan(
                "de-batch",
                JUN,
                "Junior Data Engineer",
                HYB,
                "Собираем данные со спутников, метеостанций и датчиков техники в единое хранилище.",
                17,
            ),
        ),
    ),
    CompanyPlan(
        key="streamline-media",
        name="СтримЛайн Медиа",
        industry="Медиа и видеостриминг",
        city="Москва",
        size="201–500",
        description=(
            "Онлайн-кинотеатр и сервис подкастов с 4 млн подписчиков. Собственные видеоплеер, "
            "CDN и рекомендательная система."
        ),
        vacancies=(
            VacancyPlan(
                "rust-backend",
                SEN,
                "Senior Rust-разработчик (медиасервер)",
                RMT,
                "Медиасервер раздаёт видео 4 млн подписчиков; переписываем критичные части "
                "с C++ на Rust.",
                3,
                ("FFmpeg",),
            ),
            VacancyPlan(
                "react-frontend",
                MID,
                "Frontend-разработчик (Smart TV и веб-плеер)",
                HYB,
                "Разрабатываем приложения для Smart TV и веб-плеер с адаптивным битрейтом.",
                7,
            ),
            VacancyPlan(
                "react-frontend",
                LEAD,
                "Тимлид frontend-команды",
                HYB,
                "Ведём три фронтенд-команды (12 человек): веб, Smart TV и внутренние инструменты.",
                21,
            ),
            VacancyPlan(
                "ios",
                MID,
                "iOS-разработчик (видеоплеер)",
                RMT,
                "Делаем iOS-приложение онлайн-кинотеатра: плеер, загрузки для офлайна и AirPlay.",
                10,
            ),
            VacancyPlan(
                "sre",
                MID,
                "SRE-инженер (CDN)",
                HYB,
                "Отвечаем за CDN из 40 узлов и пиковые нагрузки во время премьер.",
                14,
            ),
        ),
    ),
    CompanyPlan(
        key="promintegration",
        name="ПромИнтеграция",
        industry="Промышленная автоматизация и IIoT",
        city="Пермь",
        size="501–1000",
        description=(
            "Разрабатываем платформу промышленного интернета вещей: цифровые двойники "
            "оборудования, предиктивная аналитика и диспетчерские панели для 60 заводов."
        ),
        vacancies=(
            VacancyPlan(
                "dotnet-backend",
                SEN,
                "Senior .NET-разработчик (платформа IIoT)",
                HYB,
                "Платформа собирает телеметрию с 50 000 датчиков на заводах и строит цифровые "
                "двойники оборудования.",
                5,
            ),
            VacancyPlan(
                "de-stream",
                MID,
                "Data Engineer (потоковая телеметрия)",
                HYB,
                "Обрабатываем потоки телеметрии в реальном времени и предсказываем отказы "
                "оборудования.",
                9,
                ("ClickHouse",),
            ),
            VacancyPlan(
                "angular-frontend",
                JUN,
                "Junior Frontend-разработчик (Angular)",
                OFC,
                "Разрабатываем SCADA-дашборды для диспетчеров промышленных предприятий.",
                16,
            ),
            VacancyPlan(
                "qa-auto-python",
                MID,
                "QA Automation-инженер (Python)",
                HYB,
                "Автоматизируем тестирование платформы IIoT, включая интеграции с промышленными "
                "контроллерами.",
                20,
            ),
        ),
    ),
    CompanyPlan(
        key="travelio",
        name="Тревелио",
        industry="Travel tech",
        city="Санкт-Петербург",
        size="201–500",
        description=(
            "Сервис бронирования путешествий по России: авиабилеты, отели и туры в одном "
            "приложении. В высокий сезон обрабатываем до 30 000 бронирований в день."
        ),
        vacancies=(
            VacancyPlan(
                "php-backend",
                MID,
                "PHP-разработчик (Symfony)",
                RMT,
                "Ядро бронирования отелей на Symfony: интеграции с 200 поставщиками и миллионы "
                "цен в час.",
                4,
                ("Symfony",),
            ),
            VacancyPlan(
                "python-backend",
                SEN,
                "Senior Python-разработчик (поиск авиабилетов)",
                HYB,
                "Поиск авиабилетов опрашивает десятки поставщиков и возвращает выдачу "
                "за 2 секунды.",
                8,
                ("asyncio", "Redis"),
            ),
            VacancyPlan(
                "ios",
                JUN,
                "Junior iOS-разработчик",
                HYB,
                "Небольшая iOS-команда развивает приложение для бронирования путешествий; рядом "
                "сильные сеньоры.",
                13,
            ),
            VacancyPlan(
                "product-analytics",
                MID,
                "Аналитик данных (ценообразование)",
                HYB,
                "Ищем закономерности в спросе и помогаем формировать цены на туры и отели.",
                18,
            ),
        ),
    ),
    CompanyPlan(
        key="edarjadom",
        name="ЕдаРядом",
        industry="Foodtech: доставка еды",
        city="Москва",
        size="501–1000",
        description=(
            "Доставляем еду из ресторанов и продукты из дарксторов в среднем за 25 минут. "
            "Работаем в Москве и Подмосковье, с нами 10 000 курьеров-партнёров."
        ),
        vacancies=(
            VacancyPlan(
                "kotlin-backend",
                SEN,
                "Senior Kotlin-разработчик (диспетчеризация курьеров)",
                HYB,
                "Сервис диспетчеризации каждую секунду распределяет заказы между 10 000 курьеров.",
                3,
                ("Kafka",),
            ),
            VacancyPlan(
                "android",
                JUN,
                "Junior Android-разработчик (приложение курьера)",
                HYB,
                "Приложение курьера: маршруты, статусы заказов и выплаты; рядом опытные "
                "Android-разработчики.",
                9,
            ),
            VacancyPlan(
                "qa-auto-python",
                JUN,
                "Junior QA Automation-инженер (Python)",
                RMT,
                "Автоматизируем тестирование API заказов и оплаты; есть наставник и готовый "
                "фреймворк.",
                12,
            ),
            VacancyPlan(
                "devops",
                JUN,
                "Junior DevOps-инженер",
                HYB,
                "Инфраструктурная команда из 6 человек научит Kubernetes, Terraform и культуре "
                "дежурств.",
                16,
            ),
        ),
    ),
    CompanyPlan(
        key="kvant-analytics",
        name="Квант Аналитика",
        industry="Искусственный интеллект (LLM, NLP)",
        city="Москва",
        size="11–50",
        description=(
            "Стартап, который создаёт корпоративных ИИ-ассистентов: поиск по документам, "
            "суммаризация звонков и чат-боты на базе open source LLM. Среди клиентов — банки "
            "и промышленные холдинги."
        ),
        vacancies=(
            VacancyPlan(
                "ml-nlp",
                SEN,
                "Senior NLP/LLM-инженер",
                RMT,
                "Строим корпоративных ИИ-ассистентов для банков и промышленности на базе "
                "open source LLM.",
                2,
                ("vLLM", "RAG"),
            ),
            VacancyPlan(
                "ml-nlp",
                JUN,
                "Junior ML-инженер (NLP)",
                HYB,
                "Работа над RAG-поиском по документам вместе с сильными senior-инженерами.",
                7,
            ),
            VacancyPlan(
                "python-backend",
                MID,
                "Python-разработчик (RAG-платформа)",
                RMT,
                "Платформа индексирует миллионы документов клиентов и отвечает на вопросы "
                "сотрудников.",
                11,
                ("FastAPI", "Elasticsearch"),
            ),
            VacancyPlan(
                "ts-fullstack",
                MID,
                "Fullstack-разработчик (Next.js + Node.js)",
                RMT,
                "Делаем интерфейсы ассистентов и админ-панели для клиентов.",
                15,
                ("Next.js",),
            ),
            VacancyPlan(
                "devops",
                MID,
                "MLOps-инженер",
                HYB,
                "Готовим инфраструктуру обучения и инференса моделей на GPU-кластере.",
                None,
            ),
        ),
    ),
    CompanyPlan(
        key="stroydvor",
        name="СтройДвор",
        industry="Ритейл: товары для ремонта",
        city="Самара",
        size="5000+",
        description=(
            "Сеть из 90 гипермаркетов товаров для ремонта и дома в Поволжье и на Урале и "
            "интернет-магазин с доставкой. Развиваем собственную e-commerce-платформу."
        ),
        vacancies=(
            VacancyPlan(
                "php-backend",
                SEN,
                "Senior PHP-разработчик (интернет-магазин)",
                HYB,
                "Интернет-магазин сети: 200 000 товаров, доставка и самовывоз из 90 гипермаркетов.",
                5,
                ("Laravel",),
            ),
            VacancyPlan(
                "vue-frontend",
                JUN,
                "Junior Frontend-разработчик (Vue)",
                OFC,
                "Развиваем витрину интернет-магазина и мобильную версию сайта.",
                10,
            ),
            VacancyPlan(
                "qa-manual",
                MID,
                "QA-инженер (интернет-магазин)",
                RMT,
                "Тестируем корзину, оплату и программу лояльности перед каждым релизом.",
                14,
            ),
            VacancyPlan(
                "de-batch",
                MID,
                "Data Engineer (данные о продажах)",
                HYB,
                "Собираем данные о продажах и остатках 90 магазинов для прогнозов закупок.",
                19,
            ),
            VacancyPlan(
                "python-backend",
                LEAD,
                "Тимлид backend-разработки (Python)",
                HYB,
                "Команда e-commerce растёт: нужен тимлид для пяти backend-разработчиков и "
                "переезда на микросервисы.",
                26,
            ),
        ),
    ),
    CompanyPlan(
        key="poekhali",
        name="Поехали!",
        industry="Каршеринг и мобильность",
        city="Москва",
        size="201–500",
        description=(
            "Каршеринг в 8 городах России: 15 000 автомобилей, телематика в реальном времени и "
            "приложение с рейтингом 4,8."
        ),
        vacancies=(
            VacancyPlan(
                "go-backend",
                MID,
                "Go-разработчик (телематика)",
                HYB,
                "Телематика каждые 5 секунд принимает данные от 15 000 автомобилей и управляет "
                "замками и двигателями.",
                4,
                ("Kafka",),
            ),
            VacancyPlan(
                "ios",
                MID,
                "iOS-разработчик",
                HYB,
                "Приложение каршеринга с рейтингом 4,8: бронирование, открытие машины по "
                "Bluetooth и оплата.",
                8,
            ),
            VacancyPlan(
                "appsec",
                MID,
                "Специалист по безопасности мобильных приложений",
                RMT,
                "Защищаем приложение и телематику от угона машин и мошенничества с аккаунтами.",
                13,
            ),
            VacancyPlan(
                "de-stream",
                SEN,
                "Senior Data Engineer (телематика, стриминг)",
                HYB,
                "Потоки телеметрии — основа для ценообразования, страхования и детекции аварий.",
                17,
                ("ClickHouse",),
            ),
        ),
    ),
)
