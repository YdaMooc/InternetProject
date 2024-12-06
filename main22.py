from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import pandas as pd
import jieba
import jieba.analyse
from wordcloud import WordCloud
import matplotlib.pyplot as plt
import time
import matplotlib

matplotlib.use("TkAgg")

# 配置 Chrome 无头模式
chrome_options = Options()
chrome_options.add_argument("--headless")  # 无头模式
chrome_options.add_argument('--disable-gpu')  # 禁用 GPU
chrome_options.add_argument('window-size=1920x1080')  # 设置浏览器窗口大小

# 启动浏览器
driver = webdriver.Chrome(options=chrome_options)


# 请求重试机制，重新请求5次
def fetch_data(url, retries=5, delay=2):
    for attempt in range(retries):
        try:
            # 使用 Selenium 获取页面
            driver.get(url)
            time.sleep(3)  # 等待页面加载
            html = driver.page_source
            return html
        except Exception as e:
            print(f"请求异常: {e}")
            time.sleep(delay)
    return None  # 如果所有请求都失败，返回None


# 解析页面HTML，提取视频信息
def parse_bilibili_html(html):
    soup = BeautifulSoup(html, 'html.parser')

    rank_list = []
    title_list = []
    video_url = []
    author_list = []
    play_count_list = []
    danmu_count_list = []

    video_elements = soup.select('.rank-item')  # 根据页面的结构选择视频项的CSS类名
    print(f"匹配到的 rank-item 元素数量: {len(video_elements)}")  # 打印匹配到的视频数量

    for idx, video in enumerate(video_elements):
        try:
            rank_list.append(idx + 1)

            # 提取视频标题
            title = video.select_one('.title')
            if title:
                title_list.append(title.get_text())
            else:
                title_list.append("未知标题")

            # 提取视频链接
            link = video.select_one('a')
            if link:
                video_url.append('https://www.bilibili.com' + link['href'])
            else:
                video_url.append("未知链接")

            # 提取作者
            author = video.select_one('.up-name')
            if author:
                author_list.append(author.get_text())
            else:
                author_list.append("未知作者")

            # 提取播放数
            play_count = video.select_one('.detail-state .data-box:nth-of-type(1)')
            if play_count:
                play_count_list.append(play_count.get_text())
            else:
                play_count_list.append("0")

            # 提取弹幕数
            danmu_count = video.select_one('.detail-state .data-box:nth-of-type(2)')
            if danmu_count:
                danmu_count_list.append(danmu_count.get_text())
            else:
                danmu_count_list.append("0")
        except Exception as e:
            print(f"解析错误: {e}")
            continue

    # 使用pandas创建DataFrame，准备存储所有提取的数据
    df = pd.DataFrame({
        '排行': rank_list,
        '视频标题': title_list,
        '视频地址': video_url,
        '作者': author_list,
        '播放数': play_count_list,
        '弹幕数': danmu_count_list,
    })

    return df

# 生成词云
def generate_wordcloud(text):
    if not text.strip():
        print("没有有效的文本内容，无法生成词云")
        return

    keywords = jieba.analyse.extract_tags(text, topK=100, withWeight=False)

    if not keywords:
        print("没有提取到关键词，无法生成词云")
        return

    words_str = ' '.join(keywords)
    wordcloud = WordCloud(
        font_path='simhei.ttf',  # 字体路径，需要一个支持中文的字体文件
        width=800,
        height=400,
        background_color='white',
        max_words=200,  # 最大显示的词数
        max_font_size=150  # 最大字体大小
    ).generate(words_str)

    plt.figure(figsize=(10, 5))
    plt.imshow(wordcloud, interpolation='bilinear')
    plt.axis('off')
    plt.show()


# 数据存储
def store_data_to_csv(df, filename):
    df.to_csv(filename, index=False, encoding='utf_8_sig')


# 主程序
def main():
    url_bilibili = 'https://www.bilibili.com/ranking'
    html = fetch_data(url_bilibili)

    if html:
        # 解析页面并提取数据
        df = parse_bilibili_html(html)

        # 存储数据到 CSV
        store_data_to_csv(df, 'TOP100.csv')

        # 生成词云
        text = ' '.join(df['视频标题'])
        generate_wordcloud(text)

    # 关闭浏览器
    driver.quit()


if __name__ == "__main__":
    main()
