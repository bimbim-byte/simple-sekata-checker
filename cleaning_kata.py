import re
import pandas as pd

df = pd.read_csv('data_kata/kbbi_v.csv') 
kolom_a = df.iloc[:, 0]
pattern = re.compile(r'[^a-zA-Z\s]')

kata_list = []
for baris in kolom_a:
    if isinstance(baris, str):
        # abaikan jika ada ( atau )
        if '(' in baris or ')' in baris:
            continue
        # abaikan jika ada angka atau karakter khusus
        if pattern.search(baris):
            continue
        # split baris menjadi kata-kata
        kata_kata = baris.split()
        # abaikan jika kata pertama diawali '-'
        if kata_kata and kata_kata[0].startswith('-'):
            continue
        # tambahkan kata ke list
        kata_list.extend(kata_kata)

# Hapus duplikat dan urutkan
kata_unik = sorted(set(kata_list))

file_name = 'data_kata/kbbi_edited.txt'
with open(file_name, 'w', encoding='utf-8') as f:
    for kata in kata_unik:
        f.write(kata + '\n')

print("Pembersihan daftar kata selesai. Disimpan di {}".format(file_name))

# Data txt untuk dicopy ke html (not using internet)
with_string = ",".join(f'"{item}"' for item in kata_unik)

file_name = 'data_kata/open_and_copy.txt'
with open(file_name, 'w', encoding='utf-8') as f:
    f.write(with_string)

print("Pembersihan daftar kata selesai. Disimpan di {}".format(file_name))