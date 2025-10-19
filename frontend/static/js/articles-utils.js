// 渲染文章列表 - 直接链接到独立页面
function renderArticles(category, containerId) {
    try {
        const container = document.getElementById(containerId);
        
        // 检查 articlesData 是否存在
        if (typeof articlesData === 'undefined') {
            console.error('articlesData is not defined');
            container.innerHTML = '<p class="no-articles">数据加载失败，请刷新页面重试</p>';
            return;
        }
        
        const articles = articlesData[category] || [];
        
        console.log('Rendering articles for category:', category, 'Found:', articles.length); // 调试信息
        
        if (articles.length === 0) {
            container.innerHTML = '<p class="no-articles">暂无文章，敬请期待...</p>';
            return;
        }
        
        const articlesHTML = articles.map(article => `
            <div class="article-item" data-article-id="${article.id}">
                <div class="article-header">
                    <a href="${article.url}" class="article-title-link">
                        ${article.title}
                    </a>
                    <span class="article-meta">${article.date}</span>
                </div>
            </div>
        `).join('');
        
        container.innerHTML = articlesHTML;
    } catch (error) {
        console.error('Error rendering articles:', error);
        const container = document.getElementById(containerId);
        container.innerHTML = '<p class="no-articles">加载文章列表时出错</p>';
    }
}