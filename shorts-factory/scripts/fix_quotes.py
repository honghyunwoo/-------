"""Fix Korean quotes in JSON file"""

with open('../data/scripts_pilot_20.json', 'r', encoding='utf-8') as f:
    content = f.read()

# 한글 큰따옴표를 작은따옴표로 변경
content = content.replace('"', "'")
content = content.replace('"', "'")

with open('../data/scripts_pilot_20.json', 'w', encoding='utf-8') as f:
    f.write(content)

print('Fixed Korean quotes')
