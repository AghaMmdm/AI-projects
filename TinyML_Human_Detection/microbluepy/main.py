import machine
import sys
import math
import array

# دیگر فایل سنگین قبلی را import نمی‌کنیم، بلکه فایل کانفیگ سبک را می‌خوانیم
try:
    import model_config
except ImportError:
    print("فایل کانفیگ پیدا نشد.")

def sigmoid(x):
    if x < -70: return 0.0
    if x > 70: return 1.0
    return 1.0 / (1.0 + math.exp(-x))

def quantized_dense_layer(input_array, weights_int8, biases, scale, zero_point, input_size, output_size):
    output = array.array('f', [0.0] * output_size)
    for i in range(output_size):
        sum_val = biases[i]
        for j in range(input_size):
            w_int8 = weights_int8[j * output_size + i]
            w_float = (w_int8 - zero_point) * scale
            sum_val += input_array[j] * w_float
        output[i] = sum_val
    return output

# --- بخش جدید: خواندن مستقیم وزن‌ها از فایل باینری ---
# خواندن فایل w_6.bin (وزن‌های لایه آخر) در کسری از ثانیه
with open('w_6.bin', 'rb') as f:
    weight_data = f.read()
    
# تبدیل دیتای خام به آرایه فشرده حافظه
dense_w_compact = array.array('b', weight_data)
# ----------------------------------------------------

BUFFER_SIZE = 9216 
buffer = bytearray(BUFFER_SIZE)

while True:
    bytes_read = sys.stdin.buffer.readinto(buffer)
    
    if bytes_read == BUFFER_SIZE:
        input_data = array.array('f', (b / 255.0 for b in buffer))
        
        final_logits = quantized_dense_layer(
            input_array=input_data, 
            weights_int8=dense_w_compact, 
            biases=model_config.b_8,           # استفاده از فایل کانفیگ جدید
            scale=model_config.w_6_scale,      # استفاده از فایل کانفیگ جدید
            zero_point=model_config.w_6_zp,    # استفاده از فایل کانفیگ جدید
            input_size=16, 
            output_size=1
        )
        
        probability = sigmoid(final_logits[0])
        
        if probability > 0.5:
            print("Person")
        else:
            print("No Person")