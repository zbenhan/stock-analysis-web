// frontend/static/js/articles-utils.js

// 渲染文章列表 - 直接链接到独立页面
function renderArticles(category, containerId) {
    const container = document.getElementById(containerId);
    const articles = articlesData[category] || [];
    
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
}

// 查找相关文章
function findRelatedArticles(currentArticle, currentCategory, limit = 3) {
    const related = [];
    const currentKeywords = currentArticle.keywords || [];
    
    articlesData[currentCategory].forEach(article => {
        if (article.id !== currentArticle.id) {
            const commonKeywords = article.keywords.filter(kw => 
                currentKeywords.includes(kw)
            );
            if (commonKeywords.length > 0) {
                related.push({
                    ...article,
                    relevance: commonKeywords.length
                });
            }
        }
    });
    
    return related
        .sort((a, b) => b.relevance - a.relevance)
        .slice(0, limit);
}

