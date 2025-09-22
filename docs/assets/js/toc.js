
document.addEventListener("DOMContentLoaded", function() {
  const content = document.querySelector('.page-content');
  const tocContainer = document.createElement('nav');
  tocContainer.className = 'toc';
  
  const headings = content.querySelectorAll('h1, h2, h3, h4');
  
  if (headings.length > 1) {
    const tocList = document.createElement('ul');
    headings.forEach(heading => {
      if (heading.id) {
        const listItem = document.createElement('li');
        const link = document.createElement('a');
        link.href = '#' + heading.id;
        link.textContent = heading.textContent;
        listItem.appendChild(link);
        tocList.appendChild(listItem);
      }
    });
    tocContainer.appendChild(tocList);
    document.body.appendChild(tocContainer);
  }
});
