import tensorflow as tf
import numpy as np
import os

interpreter = tf.lite.Interpreter(model_path="model.tflite")
interpreter.allocate_tensors()

tensor_details = interpreter.get_tensor_details()

weight_counter = 0
bias_counter = 0

with open("model_config.py", "w") as f:
    f.write("# TFLite Lightweight Config\n\n")
    
    for detail in tensor_details:
        try:
            tensor_data = interpreter.get_tensor(detail['index'])
            
            # ۱. استخراج وزن‌ها (INT8) و ذخیره به عنوان فایل باینری خام
            if detail['dtype'] == np.int8:
                quantization = detail['quantization']
                scales = quantization[0]
                zero_points = quantization[1]
                
                scale = float(scales[0]) if hasattr(scales, '__len__') and len(scales) > 0 else (float(scales) if scales != 0.0 else 1.0)
                zero_point = int(zero_points[0]) if hasattr(zero_points, '__len__') and len(zero_points) > 0 else int(zero_points)
                
                # تبدیل به آرایه یک‌بعدی از جنس int8
                weights_int8 = tensor_data.flatten().astype(np.int8)
                bin_filename = f"w_{weight_counter}.bin"
                
                # ذخیره وزن‌ها در یک فایل باینری (حجم این فایل دقیقاً برابر با تعداد وزن‌هاست)
                weights_int8.tofile(bin_filename)
                
                # ذخیره اطلاعات سبک در فایل پایتون
                f.write(f"# Shape: {detail['shape']}\n")
                f.write(f"w_{weight_counter}_scale = {scale}\n")
                f.write(f"w_{weight_counter}_zp = {zero_point}\n\n")
                
                weight_counter += 1
                
            # ۲. استخراج بایاس‌ها (چون کوتاه هستند، در همان فایل متنی می‌مانند)
            elif detail['dtype'] in [np.float32, np.int32] and len(detail['shape']) == 1:
                biases = tensor_data.flatten().tolist()
                f.write(f"b_{bias_counter} = {biases}\n\n")
                bias_counter += 1
                
        except ValueError:
            pass

print("فایل‌های باینری و فایل کانفیگ با موفقیت ساخته شدند!")