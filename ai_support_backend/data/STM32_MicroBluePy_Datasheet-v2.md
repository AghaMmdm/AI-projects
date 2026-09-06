## نام و مشخصات کلی چیپ
میکروکنترلر قدرتمند STM32F405RGT6 از خانواده STM32 (دارای هسته ARM Cortex-M4 32-bit به همراه واحد ممیز شناور FPU) با حداکثر فرکانس کاری 168 MHz (با کریستال خارجی 12 MHz) کار می‌کند. این چیپ مجهز به 1 MB حافظه Flash و 192 KB حافظه SRAM (به علاوه 4 KB حافظه Backup SRAM) است. ولتاژ کاری منطقی این میکروکنترلر 3.3V است که از طریق رگولاتورهای روی برد با ورودی‌های 5V (USB) یا 6 تا 12 ولت (باتری) تامین می‌شود.

## جدول پین‌اوت کامل
| شماره پین | نام پین | عملکردهای جایگزین (Alternate Functions) | توضیح کاربردی |
|---|---|---|---|
| 1 | Vbackup | EVENTOUT | ورودی ولتاژ باتری پشتیبان (RTC) |
| 2 | X18 | OTG_HS_ULPI_STP / EVENTOUT | GPIO دیجیتال |
| 7 | RESET | - | پین ریست سخت‌افزاری |
| 8 | X19 | EVENTOUT | ADC (کانال ADC123_IN10) |
| 9 | X20 | ETH_MDC / EVENTOUT | ADC (کانال ADC123_IN11) |
| 10 | X21 | SPI2_MISO / ETH_MII_TXD2 / I2S2ext_SD / EVENTOUT | ADC / SPI2_MISO |
| 11 | X22 | SPI2_MOSI / I2S2_SD / ETH_MII_TX_CLK / EVENTOUT | ADC / SPI2_MOSI |
| 14 | X1 | USART2_CTS / UART4_TX / TIM2_CH1_ETR / TIM5_CH1 / TIM8_ETR | ADC / UART4_TX / PWM (مشترک با Motor4) |
| 15 | X2 | USART2_RTS / UART4_RX / ETH_RMII_REF_CLK / TIM5_CH2 / TIM2_CH2 | ADC / UART4_RX / PWM (مشترک با Motor3) |
| 16 | X3 | USART2_TX / TIM5_CH3 / TIM9_CH1 / TIM2_CH3 / ETH_MDIO | ADC / USART2_TX / PWM (مشترک با Motor2) |
| 17 | X4 | USART2_RX / TIM5_CH4 / TIM9_CH2 / TIM2_CH4 / OTG_HS_ULPI_D0 | ADC / USART2_RX / PWM (مشترک با Motor1) |
| 20 | X5 | SPI1_NSS / SPI3_NSS / USART2_CK / I2S3_WS / EVENTOUT | خروجی آنالوگ (DAC) / ADC / SPI1_NSS |
| 21 | X6 | SPI1_SCK / OTG_HS_ULPI_CK / TIM2_CH1_ETR / TIM8_CH1N | ADC / DAC / SPI1_SCK / PWM (مشترک با Motor3) |
| 22 | X7 | SPI1_MISO / TIM8_BKIN / TIM13_CH1 / TIM3_CH1 / TIM1_BKIN | ADC / SPI1_MISO / PWM (مشترک با Motor4) |
| 23 | X8 | SPI1_MOSI / TIM8_CH1N / TIM14_CH1 / TIM3_CH2 / TIM1_CH1N | ADC / SPI1_MOSI / PWM |
| 24 | X11 | ETH_RMII_RX_D0 / ETH_MII_RX_D0 / EVENTOUT | ADC |
| 25 | X12 | ETH_RMII_RX_D1 / ETH_MII_RX_D1 / EVENTOUT | ADC |
| 26 | Y11 | TIM3_CH3 / TIM8_CH2N / OTG_HS_ULPI_D1 / TIM1_CH2N | ADC / PWM |
| 27 | Y12 | TIM3_CH4 / TIM8_CH3N / OTG_HS_ULPI_D2 / TIM1_CH3N | ADC / PWM |
| 29 | Y9 | SPI2_SCK / I2S2_CK / I2C2_SCL / USART3_TX / TIM2_CH3 | I2C2_SCL / USART3_TX / SPI2_SCK / PWM |
| 30 | Y10 | I2C2_SDA / USART3_RX / TIM2_CH4 / EVENTOUT | I2C2_SDA / USART3_RX / PWM |
| 33 | Y5 | SPI2_NSS / I2S2_WS / I2C2_SMBA / USART3_CK / CAN2_RX | CAN2_RX / SPI2_NSS / USART3 |
| 34 | Y6 | SPI2_SCK / I2S2_CK / USART3_CTS / TIM1_CH1N / CAN2_TX | CAN2_TX / SPI2_SCK / USART3 / PWM |
| 35 | Y7 | SPI2_MISO / TIM1_CH2N / TIM12_CH1 / USART3_RTS / I2S2ext_SD | SPI2_MISO / PWM |
| 36 | Y8 | SPI2_MOSI / I2S2_SD / TIM1_CH3N / TIM8_CH3N / TIM12_CH2 | SPI2_MOSI / PWM |
| 37 | Y1 | I2S2_MCK / TIM8_CH1 / SDIO_D6 / USART6_TX / TIM3_CH1 | USART6_TX / PWM |
| 38 | Y2 | I2S3_MCK / TIM8_CH2 / SDIO_D7 / USART6_RX / TIM3_CH2 | USART6_RX / PWM |
| 46 | LED1 (PA13)| - | LED قرمز روی برد (نمایش خطا و وضعیت) |
| 47 | LED2 (PA14)| - | LED سبز روی برد |
| 50 | LED3 (PA15)| JTDI / TIM2_CH1 / SPI3_NSS | LED زرد روی برد (پشتیبانی از PWM) |
| 55 | X17 | JTDO / TRACESWO / SPI3_SCK / I2S3_CK / TIM2_CH2 / SPI1_SCK | SPI3_SCK / PWM (کلید User در برخی نسخ به PB3 متصل است) |
| 56 | LED4 (PB4) | - | LED آبی روی برد (پشتیبانی از PWM) |
| 58 | X9 | I2C1_SCL / TIM4_CH1 / CAN2_TX / USART1_TX | I2C1_SCL / USART1_TX / CAN2_TX / PWM |
| 59 | X10 | I2C1_SDA / USART1_RX / TIM4_CH2 | I2C1_SDA / USART1_RX / PWM |
| 60 | BOOT0 | - | تنظیم حالت بوت (برای DFU به 3.3V وصل شود) |
| 61 | Y3 | TIM4_CH3 / TIM10_CH1 / I2C1_SCL / CAN1_RX | I2C1_SCL / CAN1_RX / PWM (مشترک با Motor1) |
| 62 | Y4 | TIM4_CH4 / TIM11_CH1 / I2C1_SDA / CAN1_TX | I2C1_SDA / CAN1_TX / PWM (مشترک با Motor2) |

## پریفرال‌های ارتباطی

### UART/USART
* **تعداد instance/کانال موجود:** 5 کانال (USART1, USART2, USART3, UART4, USART6).
* **پین‌های مرتبط:**
  * USART1: X9 (TX), X10 (RX) - پیش‌فرض برای REPL از طریق USB.
  * USART2: X3 (TX), X4 (RX).
  * USART3: Y9 (TX), Y10 (RX).
  * UART4: X1 (TX), X2 (RX).
  * USART6: Y1 (TX), Y2 (RX).
* **محدودیت‌های سرعت/فرکانس:** نامشخص در دیتاشیت. در صورت تغییر USART پیش‌فرض از 1، اتصال REPL از طریق USB قطع خواهد شد.

### I2C
* **تعداد instance/کانال موجود:** 2 کانال ارتباط سخت‌افزاری I2C (I2C1 و I2C2).
* **پین‌های مرتبط:**
  * I2C1: X9/Y3 (SCL), X10/Y4 (SDA).
  * I2C2: Y9 (SCL), Y10 (SDA) - این باس به صورت سخت‌افزاری به نمایشگر OLED روی برد متصل است.
* **محدودیت‌های سرعت/فرکانس:** پشتیبانی تا 400kHz.

### SPI
* **تعداد instance/کانال موجود:** 2 کانال اصلی ارتباط SPI (SPI1 و SPI2).
* **پین‌های مرتبط:**
  * SPI1: X5 (NSS), X6 (SCK), X7 (MISO), X8 (MOSI).
  * SPI2: Y5 (NSS), Y6 (SCK), Y7 (MISO), Y8 (MOSI).
* **محدودیت‌های سرعت/فرکانس:** نامشخص در دیتاشیت (استفاده از 200,000 baudrate در مثال‌ها آمده است).

### ADC و DAC
* **تعداد instance/کانال موجود:** 16 کانال ADC دوازده بیتی (0 تا 4095) و 1 کانال پرکاربرد DAC.
* **پین‌های مرتبط:**
  * ADC: X1 تا X8، X11, X12, X19 تا X22، Y11, Y12.
  * DAC: پین X5 (برای تولید صوت و ولتاژ آنالوگ واقعی).
* **محدودیت‌های سرعت/فرکانس:** نامشخص در دیتاشیت. حداکثر ولتاژ قابل اندازه‌گیری آنالوگ 3.3V است.

### PWM/Timer
* **تعداد instance/کانال موجود:** 15 کانال PWM سخت‌افزاری بر پایه تایمرهای TIM1 تا TIM14.
* **پین‌های مرتبط:** تقریباً تمامی پین‌های GPIO (مثل X1 تا X8، Y1 تا Y4، Y6 تا Y12). همچنین روشنایی LED3 و LED4 با PWM قابل کنترل است.
* **محدودیت‌های سرعت/فرکانس:** فرکانس تایمرها با توجه به کلاک اصلی سیستم (تا 168MHz) تنظیم می‌شود.

### CAN و I2S
* **تعداد instance/کانال موجود:** 2 کنترلر bxCAN برای CAN-Bus و 1 باس I2S در دسترس.
* **پین‌های مرتبط:**
  * CAN1: Y3 (RX), Y4 (TX).
  * CAN2: Y5 (RX), Y6 (TX).
  * I2S (شناسه 2): مشترک با پین‌های SPI (مانند Y5, Y6, Y8).
* **محدودیت‌های سرعت/فرکانس:** واحد I2S دارای PLL اختصاصی برای تولید کلاک دقیق صوتی (مانند 44100Hz و 22050Hz) است.

## مشخصات الکتریکی کلیدی
* **محدوده ولتاژ ورودی/خروجی پین‌ها:**
  * ولتاژ ورودی و خروجی لاجیک پین‌های GPIO روی 3.3V تنظیم شده است.
  * ولتاژ ورودی باتری (Battery Vin): 6 تا 12 ولت.
  * ولتاژ ورودی USB: 4 تا 6 ولت.
* **حداکثر جریان قابل تحمل هر پین GPIO:** حداکثر 20 تا 25 میلی‌آمپر.
* **ولتاژ مرجع ADC:** ولتاژ آنالوگ کاملاً محدود به 3.3V است.

## نکات و هشدارهای سخت‌افزاری مهم
* **پین‌های 5V-tolerant و آنالوگ:** پایه‌های نوع `FT` تحمل ولتاژ ورودی 5 ولت (فقط برای دیتای دیجیتال) را دارند، اما پین‌های نوع `TTa` اکیداً 3.3V-only هستند. دقت کنید مقادیر آنالوگ (ADC) روی همه پایه‌ها فقط با ولتاژ 3.3V معتبر است.
* **تداخل درایور موتور (BlueDriver) و سنسورها:** ۴ پورت اختصاصی موتور با پایه‌های GPIO مشترک هستند:
  * Motor1 (PB8, PA3) / Motor2 (PB9, PA2) / Motor3 (PA1, PA5) / Motor4 (PA0, PA6).
  در صورت استفاده از یک موتور، از پایه‌های مجاور آن به هیچ وجه به عنوان ورودی سنسور استفاده نکنید تا مدار امنیتی فعال نشود.
* **قوانین وقفه (EXTI):** تمامی پین‌های GPIO قابلیت وقفه خارجی دارند، اما مجاز نیستید از دو پین با شماره یکسان در پورت‌های مختلف (مثلاً PA10 و PB10) همزمان برای وقفه استفاده کنید.
* **مدیریت توان و درگاه‌ها:** اتصال همزمان USB و باتری بدون خاموش کردن کلید `Digital ON/OFF` ممنوع است و باعث جریان‌کشی می‌شود. هرگز بدون اتصال باتری، موتورها را تنها از طریق USB راه‌اندازی نکنید. ورودی باتری فقط در برابر اتصال معکوس مقاوم است و در برابر اتصال کوتاه محافظتی ندارد.
* **حالت‌های Boot و ذخیره‌سازی:** 
  * برای Factory Reset، دکمه User را نگه داشته، Reset را بزنید و User را آنقدر نگه دارید تا LED سبز و قرمز همزمان روشن شوند.
  * برای ورود به مد DFU پین BOOT0 را به 3.3V متصل و Reset کنید.
  * در ویندوز همیشه پیش از Reset سخت‌افزاری، درایو USB برد را Eject کنید تا فایل‌های `main.py` از بین نروند. (پشتیبانی از کارت حافظه SD تا 1 ترابایت وجود دارد).
