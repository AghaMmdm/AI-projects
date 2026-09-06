## نام و مشخصات کلی چیپ
میکروکنترلر STM32F405RGT6 از خانواده STM32 (دارای هسته پردازشی ARM Cortex-M4 32-bit به همراه واحد ممیز شناور FPU)، با حداکثر فرکانس کلاک 168 MHz کار می‌کند. این چیپ دارای 1 MB حافظه Flash و 192 KB حافظه SRAM (به همراه 4 KB حافظه Backup SRAM) است. ولتاژ کاری پین‌های این میکروکنترلر 3.3V می‌باشد که توسط رگولاتورهای روی برد از طریق ولتاژ ورودی اصلی تامین می‌گردد.

## جدول پین‌اوت کامل
| شماره پین | نام پین (پین میکرو) | عملکردهای جایگزین (Alternate Functions) | توضیح کاربردی |
|---|---|---|---|
| 1 | Vbackup (V_BAT) | EVENTOUT | ورودی ولتاژ باتری پشتیبان (RTC) |
| 2 | X18 (PC13) | OTG_HS_ULPI_STP / EVENTOUT | پشتیبانی از خروجی‌های دیجیتال |
| 7 | RESET (NRST) | - | پین ریست سخت‌افزاری |
| 8 | X19 (PC0) | EVENTOUT | پشتیبانی از ADC (کانال ADC123_IN10) |
| 9 | X20 (PC1) | ETH_MDC / EVENTOUT | پشتیبانی از ADC (کانال ADC123_IN11) |
| 10 | X21 (PC2) | SPI2_MISO / ETH_MII_TXD2 / I2S2ext_SD / EVENTOUT | پشتیبانی از ADC / SPI2 |
| 11 | X22 (PC3) | SPI2_MOSI / I2S2_SD / ETH_MII_TX_CLK / EVENTOUT | پشتیبانی از ADC / SPI2 |
| 14 | X1 (PA0) | USART2_CTS / UART4_TX / TIM2_CH1_ETR / TIM5_CH1 / TIM8_ETR / EVENTOUT | پشتیبانی از ADC / UART4 / PWM (مشترک با Motor4) |
| 15 | X2 (PA1) | USART2_RTS / UART4_RX / ETH_RMII_REF_CLK / TIM5_CH2 / TIM2_CH2 / EVENTOUT | پشتیبانی از ADC / UART4 / PWM (مشترک با Motor3) |
| 16 | X3 (PA2) | USART2_TX / TIM5_CH3 / TIM9_CH1 / TIM2_CH3 / ETH_MDIO / EVENTOUT | پشتیبانی از ADC / USART2 / PWM (مشترک با Motor2) |
| 17 | X4 (PA3) | USART2_RX / TIM5_CH4 / TIM9_CH2 / TIM2_CH4 / OTG_HS_ULPI_D0 / EVENTOUT | پشتیبانی از ADC / USART2 / PWM (مشترک با Motor1) |
| 20 | X5 (PA4) | SPI1_NSS / SPI3_NSS / USART2_CK / I2S3_WS / EVENTOUT | پشتیبانی از ADC / خروجی آنالوگ DAC_OUT1 / SPI1 |
| 21 | X6 (PA5) | SPI1_SCK / OTG_HS_ULPI_CK / TIM2_CH1_ETR / TIM8_CH1N / EVENTOUT | پشتیبانی از ADC / DAC_OUT2 / SPI1 / PWM (مشترک با Motor3) |
| 22 | X7 (PA6) | SPI1_MISO / TIM8_BKIN / TIM13_CH1 / TIM3_CH1 / TIM1_BKIN / EVENTOUT | پشتیبانی از ADC / SPI1 / PWM (مشترک با Motor4) |
| 23 | X8 (PA7) | SPI1_MOSI / TIM8_CH1N / TIM14_CH1 / TIM3_CH2 / TIM1_CH1N / EVENTOUT | پشتیبانی از ADC / SPI1 / PWM |
| 24 | X11 (PC4) | ETH_RMII_RX_D0 / ETH_MII_RX_D0 / EVENTOUT | پشتیبانی از ADC |
| 25 | X12 (PC5) | ETH_RMII_RX_D1 / ETH_MII_RX_D1 / EVENTOUT | پشتیبانی از ADC |
| 26 | Y11 (PB0) | TIM3_CH3 / TIM8_CH2N / OTG_HS_ULPI_D1 / TIM1_CH2N / EVENTOUT | پشتیبانی از ADC / PWM |
| 27 | Y12 (PB1) | TIM3_CH4 / TIM8_CH3N / OTG_HS_ULPI_D2 / TIM1_CH3N / EVENTOUT | پشتیبانی از ADC / PWM |
| 29 | Y9 (PB10) | SPI2_SCK / I2S2_CK / I2C2_SCL / USART3_TX / TIM2_CH3 / EVENTOUT | پشتیبانی از I2C2 / USART3 / SPI2 / PWM |
| 30 | Y10 (PB11) | I2C2_SDA / USART3_RX / TIM2_CH4 / EVENTOUT | پشتیبانی از I2C2 / USART3 / PWM |
| 33 | Y5 (PB12) | SPI2_NSS / I2S2_WS / I2C2_SMBA / USART3_CK / TIM1_BKIN / CAN2_RX / EVENTOUT | پشتیبانی از CAN2 / SPI2 / USART3 |
| 34 | Y6 (PB13) | SPI2_SCK / I2S2_CK / USART3_CTS / TIM1_CH1N / CAN2_TX / EVENTOUT | پشتیبانی از CAN2 / SPI2 / USART3 / PWM (VBUS) |
| 35 | Y7 (PB14) | SPI2_MISO / TIM1_CH2N / TIM12_CH1 / USART3_RTS / I2S2ext_SD / EVENTOUT | پشتیبانی از SPI2 / PWM |
| 36 | Y8 (PB15) | SPI2_MOSI / I2S2_SD / TIM1_CH3N / TIM8_CH3N / TIM12_CH2 / EVENTOUT | پشتیبانی از SPI2 / PWM |
| 37 | Y1 (PC6) | I2S2_MCK / TIM8_CH1 / SDIO_D6 / USART6_TX / TIM3_CH1 / EVENTOUT | پشتیبانی از USART6 / PWM |
| 38 | Y2 (PC7) | I2S3_MCK / TIM8_CH2 / SDIO_D7 / USART6_RX / TIM3_CH2 / EVENTOUT | پشتیبانی از USART6 / PWM |
| 46 | LED1 (PA13) | - | LED قرمز روی برد |
| 47 | LED2 (PA14) | - | LED سبز روی برد |
| 50 | LED3 (PA15) | JTDI / TIM2_CH1 / SPI3_NSS / EVENTOUT | LED زرد روی برد (پشتیبانی از PWM) |
| 55 | X17 (PB3) | JTDO / TRACESWO / SPI3_SCK / I2S3_CK / TIM2_CH2 / SPI1_SCK / EVENTOUT | پشتیبانی از SPI3 / PWM |
| 56 | LED4 (PB4) | - | LED آبی روی برد (پشتیبانی از PWM) |
| 58 | X9 (PB6) | I2C1_SCL / TIM4_CH1 / CAN2_TX / USART1_TX / EVENTOUT | پشتیبانی از I2C1 / USART1 / CAN2 / PWM |
| 59 | X10 (PB7) | I2C1_SDA / USART1_RX / TIM4_CH2 / EVENTOUT | پشتیبانی از I2C1 / USART1 / PWM |
| 60 | BOOT0 | - | تنظیم حالت بوت میکروکنترلر |
| 61 | Y3 (PB8) | TIM4_CH3 / TIM10_CH1 / I2C1_SCL / CAN1_RX / EVENTOUT | پشتیبانی از I2C1 / CAN1 / PWM (مشترک با Motor1) |
| 62 | Y4 (PB9) | TIM4_CH4 / TIM11_CH1 / I2C1_SDA / CAN1_TX / EVENTOUT | پشتیبانی از I2C1 / CAN1 / PWM (مشترک با Motor2) |

## پریفرال‌های ارتباطی

### UART/USART
* **تعداد instance/کانال موجود:** 3 کانال ارتباط سریال USART مجزا (USART1, USART2, USART3) و پشتیبانی روی پین‌ها برای UART4 و USART6.
* **پین‌های مرتبط:**
  * USART1: X9 (TX), X10 (RX) (به صورت پیش‌فرض برای REPL متصل به USB استفاده می‌شود).
  * USART2: X3 (TX), X4 (RX)
  * USART3: Y9 (TX), Y10 (RX)
  * UART4: X1 (TX), X2 (RX)
  * USART6: Y1 (TX), Y2 (RX)
* **محدودیت‌های سرعت/فرکانس:** نامشخص در دیتاشیت.

### I2C
* **تعداد instance/کانال موجود:** 2 کانال ارتباط سریال I2C (I2C1 و I2C2).
* **پین‌های مرتبط:**
  * I2C1: X9/Y3 (SCL), X10/Y4 (SDA)
  * I2C2: Y9 (SCL), Y10 (SDA) (این باس روی برد به نمایشگر OLED 0.91 اینچی متصل است).
* **محدودیت‌های سرعت/فرکانس:** نامشخص در دیتاشیت (استاندارد I2C در مثال‌های کتابخانه 100kHz تا 400kHz ذکر شده است).

### SPI
* **تعداد instance/کانال موجود:** 2 کانال ارتباط سریال SPI (SPI1 و SPI2) بعلاوه پین‌های پشتیبان برای SPI3.
* **پین‌های مرتبط:**
  * SPI1: X6 (SCK), X7 (MISO), X8 (MOSI)
  * SPI2: Y6 (SCK), Y7 (MISO), Y8 (MOSI) یا X21 (MISO), X22 (MOSI)
* **محدودیت‌های سرعت/فرکانس:** نامشخص در دیتاشیت.

### ADC
* **تعداد instance/کانال موجود:** 16 کانال مبدل آنالوگ به دیجیتال، 12 بیتی (ADC123 و ADC12).
* **پین‌های مرتبط:**
  * پین‌های X1, X2, X3, X4, X5, X6, X7, X8
  * پین‌های X11, X12, X19, X20, X21, X22
  * پین‌های Y11, Y12
* **محدودیت‌های سرعت/فرکانس:** سرعت نمونه‌برداری بالا (دقیق‌تر: نامشخص در دیتاشیت).

### PWM/Timer
* **تعداد instance/کانال موجود:** 15 کانال PWM برای کنترل موتور و سایر تجهیزات.
* **پین‌های مرتبط:** اکثر پین‌های GPIO که عملکردهای جایگزین خانواده تایمرها (TIM1 تا TIM14) را دارند؛ از جمله X1 تا X8، Y1 تا Y4، Y6 تا Y12، X9, X10, X17 و LEDهای زرد (LED3) و آبی (LED4).
* **محدودیت‌های سرعت/فرکانس:** نامشخص در دیتاشیت.

### DMA
* **تعداد instance/کانال موجود:** نامشخص در دیتاشیت.
* **پین‌های مرتبط:** نامشخص در دیتاشیت.
* **محدودیت‌های سرعت/فرکانس:** نامشخص در دیتاشیت.

## مشخصات الکتریکی کلیدی
* **محدوده ولتاژ ورودی/خروجی پین‌ها:**
  * ولتاژ ورودی پین‌های GPIO (Input Volt): 0 تا 3.3V (حداکثر 3.5V).
  * ولتاژ خروجی پین‌های GPIO (Output Volt): 0 تا 3.3V (حداکثر 3.4V).
* **حداکثر جریان قابل تحمل هر پین GPIO:** 25 mA (میلی‌آمپر).
* **ولتاژ مرجع ADC:** متصل به ولتاژ داخلی 3.3V.

## نکات و هشدارهای سخت‌افزاری مهم
* **پین‌های 5V-tolerant:** پین‌هایی که نوع آن‌ها `FT` (Five-Tolerant) است، قادر به تحمل ولتاژ ورودی تا 5V هستند. اما پین‌های نوع `TTa` فقط و فقط 3.3V-only بوده و اعمال 5V به آن‌ها آسیب می‌زند. مقادیر آنالوگ (ADC) روی پین‌های FT با ولتاژ 5V نیز خطا داده و باید با 3.3V راه‌اندازی شوند.
* **تداخل پین‌های موتور و سنسورها:** 4 پورت اختصاصی برای موتورهای BlueDriver وجود دارد که با پین‌های عمومی GPIO مشترک هستند. در صورت استفاده از موتور، نباید از پین‌های مجاور آن استفاده کنید:
  * Motor1 مشترک با Y3 (PB8) و X4 (PA3)
  * Motor2 مشترک با Y4 (PB9) و X3 (PA2)
  * Motor3 مشترک با X2 (PA1) و X6 (PA5)
  * Motor4 مشترک با X1 (PA0) و X7 (PA6)
* **پین BOOT0:** اتصال این پین به 3.3V و فشردن همزمان دکمه Reset باعث ورود میکروکنترلر به حالت DFU (ارتقا و دیباگ) می‌شود.
* **پین‌های رزروشده:** پایه‌هایی از میکروکنترلر که در جدول اصلی دیتاشیت ذکر نشده‌اند (یا روی برد به صورت پین نری در دسترس نیستند)، به عملکردهای داخلی (تغذیه، اسیلاتور و غیره) اختصاص دارند و استفاده از آن‌ها مجاز نیست.
* **اخطار تامین انرژی:** به هیچ عنوان موتورهای خود را بدون اتصال باتری و فقط از طریق درگاه USB روشن نکنید، زیرا موجب فعال شدن مدار امنیتی USB خواهد شد. در صورت استفاده همزمان از کابل USB و باتری، کلید `Digital ON/OFF` باید در حالت خاموش (0) قرار گیرد تا از جریان‌کشی و آسیب جلوگیری شود.
* **خطرات ولتاژ باتری:** پورت ورودی باتری به جز در برابر اتصال معکوس قطب‌ها (Reverse Polarity)، در برابر اتصال کوتاه یا ولتاژهای غیرمتعارف بالاتر از 12 ولت محافظت نشده است و ممکن است باعث خرابی شود.
