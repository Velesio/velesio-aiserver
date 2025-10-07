/**
 * Simple client-side search functionality for Jekyll sites
 * Uses a lightweight search implementation without external dependencies
 */

class DocumentationSearch {
  constructor() {
    this.searchData = [];
    this.searchInput = document.getElementById('search-input');
    this.searchResults = document.getElementById('search-results');
    this.isInitialized = false;
    
    if (this.searchInput && this.searchResults) {
      this.init();
    }
  }
  
  async init() {
    try {
      await this.loadSearchData();
      this.bindEvents();
      this.isInitialized = true;
    } catch (error) {
      console.error('Failed to initialize search:', error);
    }
  }
  
  async loadSearchData() {
    const response = await fetch('/velesio-aiserver/search.json');
    const data = await response.json();
    
    // Flatten all content into searchable items
    this.searchData = [
      ...data.posts.map(item => ({ ...item, type: 'post' })),
      ...data.pages.map(item => ({ ...item, type: 'page' })),
      ...data.components.map(item => ({ ...item, type: 'component' })),
      ...data.unity_integrations.map(item => ({ ...item, type: 'unity_integration' }))
    ].filter(item => item.title && item.content);
  }
  
  bindEvents() {
    let searchTimeout;
    
    this.searchInput.addEventListener('input', (e) => {
      clearTimeout(searchTimeout);
      const query = e.target.value.trim();
      
      if (query.length < 2) {
        this.hideResults();
        return;
      }
      
      // Debounce search
      searchTimeout = setTimeout(() => {
        this.performSearch(query);
      }, 300);
    });
    
    this.searchInput.addEventListener('focus', () => {
      const query = this.searchInput.value.trim();
      if (query.length >= 2) {
        this.performSearch(query);
      }
    });
    
    // Hide results when clicking outside
    document.addEventListener('click', (e) => {
      if (!e.target.closest('.search-container')) {
        this.hideResults();
      }
    });
    
    // Handle keyboard navigation
    this.searchInput.addEventListener('keydown', (e) => {
      if (e.key === 'Escape') {
        this.hideResults();
      } else if (e.key === 'ArrowDown') {
        e.preventDefault();
        this.navigateResults('down');
      } else if (e.key === 'ArrowUp') {
        e.preventDefault();
        this.navigateResults('up');
      } else if (e.key === 'Enter') {
        e.preventDefault();
        this.selectResult();
      }
    });
  }
  
  performSearch(query) {
    const results = this.searchContent(query);
    this.displayResults(results, query);
  }
  
  searchContent(query) {
    const queryWords = query.toLowerCase().split(/\s+/).filter(word => word.length > 1);
    const results = [];
    
    for (const item of this.searchData) {
      const title = item.title.toLowerCase();
      const content = item.content.toLowerCase();
      const excerpt = item.excerpt ? item.excerpt.toLowerCase() : '';
      
      let score = 0;
      let matchedWords = 0;
      
      for (const word of queryWords) {
        // Title matches are weighted more heavily
        if (title.includes(word)) {
          score += 10;
          matchedWords++;
          
          // Exact title match gets even higher score
          if (title === word) {
            score += 20;
          }
        }
        
        // Content matches
        if (content.includes(word)) {
          score += 1;
          matchedWords++;
        }
        
        // Excerpt matches (moderate weight)
        if (excerpt.includes(word)) {
          score += 3;
          matchedWords++;
        }
      }
      
      // Only include results that match at least one word
      if (matchedWords > 0) {
        // Boost score if multiple words match
        score *= (matchedWords / queryWords.length);
        
        results.push({
          ...item,
          score,
          matchedWords
        });
      }
    }
    
    // Sort by score (descending) and return top 10
    return results
      .sort((a, b) => b.score - a.score)
      .slice(0, 10);
  }
  
  displayResults(results, query) {
    if (results.length === 0) {
      this.searchResults.innerHTML = '<div class="no-results">No results found</div>';
    } else {
      this.searchResults.innerHTML = results
        .map((result, index) => this.createResultHTML(result, query, index))
        .join('');
    }
    
    this.showResults();
  }
  
  createResultHTML(result, query, index) {
    const title = this.highlightMatches(result.title, query);
    const excerpt = this.highlightMatches(result.excerpt || '', query);
    const typeLabel = this.getTypeLabel(result.type);
    
    return `
      <div class="search-result-item" data-index="${index}" data-url="${result.url}">
        <div class="search-result-title">${title}</div>
        <div class="search-result-excerpt">${excerpt}</div>
        <div class="search-result-url">${typeLabel} • ${result.url}</div>
      </div>
    `;
  }
  
  highlightMatches(text, query) {
    if (!text) return '';
    
    const queryWords = query.toLowerCase().split(/\s+/).filter(word => word.length > 1);
    let highlightedText = text;
    
    for (const word of queryWords) {
      const regex = new RegExp(`(${this.escapeRegex(word)})`, 'gi');
      highlightedText = highlightedText.replace(regex, '<span class="search-highlight">$1</span>');
    }
    
    return highlightedText;
  }
  
  escapeRegex(string) {
    return string.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
  }
  
  getTypeLabel(type) {
    const labels = {
      'post': 'Blog Post',
      'page': 'Documentation',
      'component': 'Component',
      'unity_integration': 'Unity Integration'
    };
    return labels[type] || 'Page';
  }
  
  showResults() {
    this.searchResults.style.display = 'block';
    this.currentSelectedIndex = -1;
  }
  
  hideResults() {
    this.searchResults.style.display = 'none';
    this.currentSelectedIndex = -1;
  }
  
  navigateResults(direction) {
    const items = this.searchResults.querySelectorAll('.search-result-item');
    if (items.length === 0) return;
    
    // Remove current selection
    if (this.currentSelectedIndex >= 0) {
      items[this.currentSelectedIndex].classList.remove('selected');
    }
    
    // Update index
    if (direction === 'down') {
      this.currentSelectedIndex = Math.min(this.currentSelectedIndex + 1, items.length - 1);
    } else {
      this.currentSelectedIndex = Math.max(this.currentSelectedIndex - 1, -1);
    }
    
    // Add new selection
    if (this.currentSelectedIndex >= 0) {
      items[this.currentSelectedIndex].classList.add('selected');
      items[this.currentSelectedIndex].scrollIntoView({ block: 'nearest' });
    }
  }
  
  selectResult() {
    const items = this.searchResults.querySelectorAll('.search-result-item');
    if (this.currentSelectedIndex >= 0 && items[this.currentSelectedIndex]) {
      const url = items[this.currentSelectedIndex].dataset.url;
      window.location.href = url;
    }
  }
}

// Initialize search when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
  new DocumentationSearch();
});

// Add click handlers for search results
document.addEventListener('click', (e) => {
  const resultItem = e.target.closest('.search-result-item');
  if (resultItem) {
    const url = resultItem.dataset.url;
    window.location.href = url;
  }
});

// Add styles for selected search result
const searchStyles = document.createElement('style');
searchStyles.textContent = `
  .search-result-item.selected {
    background-color: var(--hover-bg, rgba(0, 122, 204, 0.2)) !important;
  }
`;
document.head.appendChild(searchStyles);