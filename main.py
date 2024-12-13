import requests
import pandas as pd
import jieba
import jieba.analyse  # 用于提取关键词
from bs4 import BeautifulSoup
from wordcloud import WordCloud
import matplotlib.pyplot as plt
import matplotlib
from matplotlib import rcParams
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

# 使用 TkAgg 后端来渲染图形
matplotlib.use("TkAgg")

# 设置中文字体和解决负号显示问题
rcParams['font.sans-serif'] = ['Microsoft YaHei']  # 设置显示中文的字体
rcParams['axes.unicode_minus'] = False  # 解决负号显示问题

# 使用 Session 来保持会话，提高请求效率
session = requests.Session()

# 配置 Chrome 浏览器的无头模式（不显示浏览器窗口）
chrome_options = Options()
chrome_options.add_argument("--headless")  # 启动无头模式，意味着浏览器不会弹出窗口
chrome_options.add_argument('--enable-gpu')  # 启用 GPU 加速
chrome_options.add_argument('window-size=1920x1080')  # 设置浏览器窗口大小

# 启动 Chrome 浏览器实例
driver = webdriver.Chrome(options=chrome_options)


def fetch_data(url, headers=None, retries=5, delay=2, method='requests'):
    """
    通用数据获取函数，支持 requests 和 selenium 两种方式。

    :param url: 请求的 URL。
    :param headers: 请求头（仅在 requests 模式下使用）。
    :param retries: 重试次数。
    :param delay: 每次重试的间隔时间（秒）。
    :param method: 数据获取方式，'requests' 或 'selenium'。
    :return: 请求到的数据（JSON 或 HTML）。
    """
    for attempt in range(retries):
        try:
            if method == 'requests':
                # 使用 requests 获取数据
                if headers is None:
                    headers = {'User-Agent': 'Mozilla/5.0'}
                response = session.get(url, headers=headers)
                if response.status_code == 200:
                    return response.json()  # 返回 JSON 数据
                else:
                    print(f"请求失败，状态码: {response.status_code}")
            elif method == 'selenium':
                # 使用 Selenium 获取页面 HTML
                driver.get(url)
                time.sleep(3)  # 等待页面加载
                return driver.page_source  # 返回页面 HTML
            else:
                print("无效的请求方式，请选择 'requests' 或 'selenium'。")
                return None
        except Exception as e:
            print(f"请求异常（{method} 模式）: {e}")
            time.sleep(delay)  # 等待后重试
    return None  # 如果所有请求都失败，返回 None


def parse_bilibili_html(html):
    """
    解析B站页面HTML，提取视频信息。

    :param html: 页面HTML内容。
    :return: 包含视频信息的DataFrame。
    """
    soup = BeautifulSoup(html, 'html.parser')  # 使用BeautifulSoup解析HTML

    # 初始化视频信息的空列表
    rank_list = []
    title_list = []
    video_url = []
    author_list = []
    play_count_list = []
    danmu_count_list = []

    # 提取每个视频的元素
    video_elements = soup.select('.rank-item')  # 根据页面的结构选择视频项的CSS类名
    print(f"匹配到的 rank-item 元素数量: {len(video_elements)}")  # 打印匹配到的视频数量

    # 遍历每个视频元素并提取信息
    for idx, video in enumerate(video_elements):
        try:
            rank_list.append(idx + 1)  # 添加视频的排名

            # 提取视频标题
            title = video.select_one('.title')
            if title:
                title_list.append(title.get_text())  # 获取标题文本
            else:
                title_list.append("未知标题")

            # 提取视频链接
            link = video.select_one('a')
            if link:
                video_url.append('https://www.bilibili.com' + link['href'])  # 获取视频地址
            else:
                video_url.append("未知链接")

            # 提取作者
            author = video.select_one('.up-name')
            if author:
                author_list.append(author.get_text())  # 获取作者名称
            else:
                author_list.append("未知作者")

            # 提取播放数
            play_count = video.select_one('.detail-state .data-box:nth-of-type(1)')
            if play_count:
                play_count_list.append(play_count.get_text())  # 获取播放数
            else:
                play_count_list.append("0")

            # 提取弹幕数
            danmu_count = video.select_one('.detail-state .data-box:nth-of-type(2)')
            if danmu_count:
                danmu_count_list.append(danmu_count.get_text())  # 获取弹幕数
            else:
                danmu_count_list.append("0")
        except Exception as e:
            print(f"解析错误: {e}")
            continue  # 如果某个视频出现错误，跳过并继续处理其他视频

    # 使用pandas创建DataFrame，准备存储所有提取的数据
    df = pd.DataFrame({
        '排行': rank_list,
        '视频标题': title_list,
        '视频地址': video_url,
        '作者': author_list,
        '播放数': play_count_list,
        '弹幕数': danmu_count_list,
    })

    return df  # 返回包含视频数据的DataFrame


def fetch_bilibili_data(url, headers):
    """
    爬取B站数据并存储为CSV文件。

    :param url: B站API的URL。
    :param headers: 请求头。
    """
    # 获取数据
    data = fetch_data(url, headers)

    # 如果数据请求成功
    if data:
        # 从响应数据中提取视频列表
        video_list = data['data']['list']

        # 初始化空列表以存储视频信息
        rank_list = []  # 排行
        title_list = []  # 视频标题
        play_cnt_list = []  # 播放数
        danmu_cnt_list = []  # 弹幕数
        coin_cnt_list = []  # 投币数
        like_cnt_list = []  # 点赞数
        share_cnt_list = []  # 分享数
        favorite_cnt_list = []  # 收藏数
        author_list = []  # 作者
        video_url = []  # 视频地址

        # 遍历视频列表并提取每部视频的信息
        for idx, video in enumerate(video_list):
            rank_list.append(idx + 1)  # 添加视频排名
            title_list.append(video['title'])  # 添加视频标题
            play_cnt_list.append(video['stat']['view'])  # 添加播放数
            danmu_cnt_list.append(video['stat']['danmaku'])  # 添加弹幕数
            coin_cnt_list.append(video['stat']['coin'])  # 添加投币数
            like_cnt_list.append(video['stat']['like'])  # 添加点赞数
            share_cnt_list.append(video['stat']['share'])  # 添加分享数
            favorite_cnt_list.append(video['stat']['favorite'])  # 添加收藏数
            author_list.append(video['owner']['name'])  # 添加作者名称
            video_url.append(f'https://www.bilibili.com/video/{video["bvid"]}')  # 添加视频地址

        # 使用pandas创建DataFrame，准备存储所有提取的数据
        df = pd.DataFrame({
            '排行': rank_list,
            '视频标题': title_list,
            '视频地址': video_url,
            '作者': author_list,
            '播放数': play_cnt_list,
            '弹幕数': danmu_cnt_list,
            '硬币数': coin_cnt_list,
            '点赞数': like_cnt_list,
            '分享数': share_cnt_list,
            '收藏数': favorite_cnt_list,
        })

        # 将DataFrame保存为CSV文件，不包含索引，使用utf_8编码
        df.to_csv('TOP100.csv', index=False, encoding="utf_8")


def generate_wordcloud(text):
    """
    生成并显示词云图。

    :param text: 用于生成词云的文本。
    """
    # 使用 jieba 提取关键词
    keywords = jieba.analyse.extract_tags(text, topK=100, withWeight=False)

    # 生成词云图
    words_str = ' '.join(keywords)
    wordcloud = WordCloud(
        font_path='simhei.ttf',  # 字体路径，需要一个支持中文的字体文件
        width=800,
        height=400,
        background_color='white',
        max_words=200,  # 最大显示的词数
        max_font_size=150  # 最大字体大小
    ).generate(words_str)

    # 显示词云图
    plt.figure(figsize=(10, 5))
    plt.imshow(wordcloud, interpolation='bilinear')
    plt.axis('off')  # 去除坐标轴
    plt.show()  # 展示词云


def store_data_to_csv(df, filename):
    """
    将DataFrame数据存储到CSV文件。

    :param df: 包含数据的DataFrame。
    :param filename: 保存的CSV文件名。
    """
    df.to_csv(filename, index=False, encoding='utf_8')  # 将数据保存为CSV文件


def clean_and_convert_to_int(value):
    """
    清理并转换播放数或弹幕数为整数。

    :param value: 原始的播放数或弹幕数字符串。
    :return: 转换后的整数值。
    """
    # 去除多余的换行符和空格
    value = value.replace('\n', '').replace(' ', '').replace(',', '')

    # 处理“万”字
    if '万' in value:
        value = value.replace('万', '')  # 去掉“万”字
        try:
            # 转换为整数，乘以10000
            return float(value) * 10000
        except ValueError:
            return 0  # 如果转换失败，返回0
    else:
        try:
            # 如果没有“万”字，直接转换为整数
            return int(value)
        except ValueError:
            return 0  # 如果转换失败，返回0


def plot_top10_by_views(file_path):
    """
    根据播放数绘制前十名视频的柱状图。

    :param file_path: 包含视频数据的CSV文件路径。
    """
    df = pd.read_csv(file_path, encoding='utf_8_sig')  # 读取CSV文件

    # 确保播放数为字符串类型，并清理转换为整数
    df['播放数'] = df['播放数'].astype(str).apply(clean_and_convert_to_int)

    # 按播放数降序排序并取前10
    top10 = df.sort_values(by='播放数', ascending=False).head(10)

    # 增大图形尺寸，适应长标题
    plt.figure(figsize=(13, 8))

    # 自动换行函数
    def wrap_labels(title, max_len=20):
        """将标题换行，防止过长标题显示不全"""
        return '\n'.join([title[i:i + max_len] for i in range(0, len(title), max_len)])

    # 为每个视频标题添加换行
    top10['视频标题'] = top10['视频标题'].apply(lambda x: wrap_labels(x, max_len=20))

    # 绘制水平柱状图
    plt.barh(top10['视频标题'], top10['播放数'])
    plt.xlabel('播放数')  # X轴标签
    plt.ylabel('视频标题')  # Y轴标签
    plt.title('播放数前10名视频')  # 图表标题

    # 设置Y轴标签字体大小
    plt.yticks(top10['视频标题'], fontsize=10)

    # 翻转 Y 轴，使得播放数最高的视频在顶部
    plt.gca().invert_yaxis()

    # 调整图表布局，确保所有元素都显示完整
    plt.tight_layout()

    # 手动调整左右边距，确保标签显示完整
    plt.subplots_adjust(left=0.3, right=0.9)

    plt.show()  # 显示图表


def first():
    """
    使用B站API爬取TOP100视频数据，并生成词云和播放数柱状图。
    """
    # B站API请求URL，用于获取排名数据
    url_bilibili = 'https://api.bilibili.com/x/web-interface/ranking/v2?rid=0&type=all'
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36 Edg/131.0.0.0'
    }
    # 获取TOP100数据
    data_TOP100 = fetch_data(url_bilibili, headers, method='requests')
    if data_TOP100:
        # 从响应数据中提取视频列表
        video_list = data_TOP100['data']['list']

        # 初始化空列表以存储视频信息
        rank_list = []  # 排行
        title_list = []  # 视频标题
        play_cnt_list = []  # 播放数
        danmu_cnt_list = []  # 弹幕数
        coin_cnt_list = []  # 投币数
        like_cnt_list = []  # 点赞数
        share_cnt_list = []  # 分享数
        favorite_cnt_list = []  # 收藏数
        author_list = []  # 作者
        video_url = []  # 视频地址

        # 遍历视频列表并提取每部视频的信息
        for idx, video in enumerate(video_list):
            rank_list.append(idx + 1)  # 添加视频排名
            title_list.append(video['title'])  # 添加视频标题
            play_cnt_list.append(video['stat']['view'])  # 添加播放数
            danmu_cnt_list.append(video['stat']['danmaku'])  # 添加弹幕数
            coin_cnt_list.append(video['stat']['coin'])  # 添加投币数
            like_cnt_list.append(video['stat']['like'])  # 添加点赞数
            share_cnt_list.append(video['stat']['share'])  # 添加分享数
            favorite_cnt_list.append(video['stat']['favorite'])  # 添加收藏数
            author_list.append(video['owner']['name'])  # 添加作者名称
            video_url.append(f'https://www.bilibili.com/video/{video["bvid"]}')  # 添加视频地址

        # 使用pandas创建DataFrame，准备存储所有提取的数据
        df = pd.DataFrame({
            '排行': rank_list,
            '视频标题': title_list,
            '视频地址': video_url,
            '作者': author_list,
            '播放数': play_cnt_list,
            '弹幕数': danmu_cnt_list,
            '硬币数': coin_cnt_list,
            '点赞数': like_cnt_list,
            '分享数': share_cnt_list,
            '收藏数': favorite_cnt_list,
        })

        # 将DataFrame保存为CSV文件，不包含索引，使用utf_8编码
        store_data_to_csv(df, 'TOP100_1.csv')

        # 生成词云
        text = ' '.join(df['视频标题'])  # 将所有视频标题合并为一个字符串
        generate_wordcloud(text)  # 生成并显示词云

        # 绘制播放数前10名的柱状图
        plot_top10_by_views('TOP100_1.csv')


def second():
    """
    使用Selenium爬取B站网页数据，并生成词云和播放数柱状图。
    """
    # B站网页排名页面URL
    url_bilibili = 'https://www.bilibili.com/v/popular/rank/all/'
    # 使用Selenium获取页面HTML
    html = fetch_data(url_bilibili, method='selenium')

    if html:
        # 解析页面并提取数据
        df = parse_bilibili_html(html)

        # 存储数据到 CSV
        store_data_to_csv(df, 'TOP100_2.csv')

        # 生成词云
        text = ' '.join(df['视频标题'])  # 将所有视频标题合并为一个字符串
        generate_wordcloud(text)  # 生成并显示词云

        # 绘制播放数前10名的柱状图
        plot_top10_by_views('TOP100_2.csv')

    # 关闭浏览器
    driver.quit()


# 主程序入口
def main():
    try:
        print("执行 API 数据爬取...")
        first()  # 执行使用API爬取数据的函数
    except Exception as e:
        print(f"API 数据爬取出错: {e}")  # 捕捉并打印API爬取中的错误

    try:
        print("执行网页数据爬取...")
        second()  # 执行使用Selenium爬取数据的函数
    except Exception as e:
        print(f"网页数据爬取出错: {e}")  # 捕捉并打印网页爬取中的错误


if __name__ == "__main__":
    main()  # 调用主函数，开始程序执行
