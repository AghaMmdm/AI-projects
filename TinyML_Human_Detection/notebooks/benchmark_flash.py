import os
import time

def flash_conv2d_3x3_laptop(in_file, out_file, weight_file, biases, scale, zp, in_w, in_h, in_c, out_c):
    """
    نسخه بهینه‌شده برای تست بنچمارک پردازش فایل‌محور
    """
    with open(out_file, 'wb') as f_out, open(in_file, 'rb') as f_in, open(weight_file, 'rb') as f_w:
        
        for y in range(in_h):
            for x in range(in_w):
                pixel_out = bytearray(out_c)
                
                for f in range(out_c):
                    sum_val = biases[f]
                    
                    for ky in [-1, 0, 1]:
                        for kx in [-1, 0, 1]:
                            iy = y + ky
                            ix = x + kx
                            
                            # کنترل مرزهای تصویر (Padding=Same)
                            if 0 <= iy < in_h and 0 <= ix < in_w:
                                for c in range(in_c):
                                    # خواندن یک پیکسل از تصویر
                                    p_idx = (iy * in_w * in_c) + (ix * in_c) + c
                                    f_in.seek(p_idx)
                                    p_byte = f_in.read(1)
                                    if not p_byte: continue
                                    p_val = float(p_byte[0]) / 255.0
                                    
                                    # خواندن یک بایت وزن مربوطه
                                    w_ky = ky + 1
                                    w_kx = kx + 1
                                    w_idx = (f * 3 * 3 * in_c) + (w_ky * 3 * in_c) + (w_kx * in_c) + c
                                    f_w.seek(w_idx)
                                    w_byte = f_w.read(1)
                                    if not w_byte: continue
                                    
                                    # دیکوانتیزه و ضرب و جمع (MAC)
                                    w_int8 = int(w_byte[0])
                                    if w_int8 > 127: w_int8 -= 256
                                    w_float = (w_int8 - zp) * scale
                                    
                                    sum_val += p_val * w_float
                    
                    # تابع فعال‌ساز ReLU
                    if sum_val < 0: sum_val = 0
                    
                    # تبدیل مجدد به بایت برای فایل خروجی
                    out_byte_val = int(sum_val) 
                    if out_byte_val > 255: out_byte_val = 255
                    
                    pixel_out[f] = out_byte_val
                
                # نوشتن آرایه ۸ بایتیِ این پیکسل در فایل
                f_out.write(pixel_out)


def flash_maxpool2d_2x2_laptop(in_file, out_file, in_w, in_h, channels):
    """
    لایه پولینگ فایل‌محور
    """
    out_w = in_w // 2
    out_h = in_h // 2
    
    with open(out_file, 'wb') as f_out, open(in_file, 'rb') as f_in:
        for y in range(out_h):
            for x in range(out_w):
                pixel_out = bytearray(channels)
                
                for c in range(channels):
                    max_val = 0
                    for ky in [0, 1]:
                        for kx in [0, 1]:
                            iy = (y * 2) + ky
                            ix = (x * 2) + kx
                            
                            p_idx = (iy * in_w * channels) + (ix * channels) + c
                            f_in.seek(p_idx)
                            p_byte = f_in.read(1)
                            if p_byte and p_byte[0] > max_val:
                                max_val = p_byte[0]
                                
                    pixel_out[c] = max_val
                f_out.write(pixel_out)


if __name__ == "__main__":
    print("=== شروع تست بنچمارک Flash-to-Flash روی لپ‌تاپ ===")
    
    if not os.path.exists('sample_image.bin') or not os.path.exists('conv1_w.bin'):
        print("خطا: فایل‌های sample_image.bin یا conv1_w.bin یافت نشدند.")
        exit()

    total_start_time = time.time()
    
    # مقادیر دقیق استخراج شده
    exact_biases = [1649, -20843, 4720, -509, -1472, -2016, 20311, 6410]
    # از یک scale کوچک فرضی استفاده می‌کنیم تا محاسبات صفر نشوند
    exact_scale = 0.01 
    exact_zp = 0
    
    # ---------------------------------------------------------
    # تست لایه ۱: Conv2D
    # ---------------------------------------------------------
    print("\nدر حال پردازش لایه 1 (Conv2D)...")
    conv_start = time.time()
    
    flash_conv2d_3x3_laptop(
        in_file='sample_image.bin', 
        out_file='layer1_conv.bin', 
        weight_file='conv1_w.bin', 
        biases=exact_biases, 
        scale=exact_scale, 
        zp=exact_zp, 
        in_w=96, in_h=96, in_c=1, out_c=8
    )
    
    conv_end = time.time()
    conv_duration = conv_end - conv_start
    print(f"زمان کانولوشن: {conv_duration:.2f} ثانیه")
    print(f"حجم فایل خروجی کانولوشن: {os.path.getsize('layer1_conv.bin')} بایت")

    # ---------------------------------------------------------
    # تست لایه ۲: Max Pooling
    # ---------------------------------------------------------
    print("\nدر حال پردازش لایه 2 (MaxPooling)...")
    pool_start = time.time()
    
    flash_maxpool2d_2x2_laptop(
        in_file='layer1_conv.bin', 
        out_file='layer1_pool.bin', 
        in_w=96, in_h=96, channels=8
    )
    
    pool_end = time.time()
    pool_duration = pool_end - pool_start
    print(f"زمان پولینگ: {pool_duration:.2f} ثانیه")
    print(f"حجم فایل خروجی پولینگ: {os.path.getsize('layer1_pool.bin')} بایت")

    # ---------------------------------------------------------
    # گزارش نهایی
    # ---------------------------------------------------------
    total_duration = time.time() - total_start_time
    print("\n" + "="*45)
    print(f"زمان کل اجرای بلوک اول: {total_duration:.2f} ثانیه")
    print("="*45)