async function fetchData(){
  const res = await fetch('data/objects.json');
  return res.json();
}

function createCard(obj){
  const el = document.createElement('article');
  el.className = 'card';
  // store categories as comma-separated string for simple DOM lookup
  const cats = Array.isArray(obj.category) ? obj.category : [obj.category];
  el.setAttribute('data-categories', cats.join(','));
  // image handling: allow absolute URL, site-relative (/), or filename stored in site/static/img
  let imgSrc = '/static/img/placeholder.jpg';
  if (obj.image && typeof obj.image === 'string'){
    const s = obj.image.trim();
    if (s.startsWith('http://') || s.startsWith('https://') || s.startsWith('/')) imgSrc = s;
    else imgSrc = 'static/img/' + s; // relative filename in site/static/img
  }
  el.innerHTML = `
    <img src="${imgSrc}" alt="${obj.title}">
    <h3>${obj.title}</h3>
    <p>${obj.description}</p>
    <p class="meta">კატეგორიები: ${cats.join(', ')}</p>
    <a class="btn" href="details.html?id=${encodeURIComponent(obj.id)}">გადასვლა დეტალებზე</a>
  `;
  return el;
}

function renderCategories(items){
  // collect unique categories (items may have category string or array)
  const all = items.flatMap(i=> Array.isArray(i.category) ? i.category : [i.category]);
  const cats = Array.from(new Set(all.filter(Boolean)));
  const leftUl = document.getElementById('category-list-left');
  const rightUl = document.getElementById('category-list-right');
  leftUl.innerHTML = '';
  rightUl.innerHTML = '';
  // simple heuristic: categories containing 'tla' or 'dzveli' or 'axali' go to right (time-based)
  cats.forEach(c=>{
    const li = document.createElement('li');
    const safe = c.replace(/\"/g, '&quot;');
    const html = `<label><input type="checkbox" class="cat-chk" value="${safe}"> ${c}</label>`;
    const lowered = c.toLowerCase();
    if (lowered.includes('tla') || lowered.includes('dzveli') || lowered.includes('axali')){
      li.innerHTML = html;
      rightUl.appendChild(li);
    } else {
      li.innerHTML = html;
      leftUl.appendChild(li);
    }
  });
  // when any checkbox changes, reapply filters
  [leftUl, rightUl].forEach(ul=> ul.addEventListener('change', (e)=>{
    if (e.target && e.target.classList.contains('cat-chk')) applyFilters();
  }));
}

let ITEMS = [];

function applyFilters(){
  const q = document.getElementById('search').value.trim().toLowerCase();
  // Left and right checkbox groups (assume left list has id 'category-list-left' and right 'category-list-right')
  const leftChecked = Array.from(document.querySelectorAll('#category-list-left .cat-chk:checked')).map(cb=>cb.value);
  const rightChecked = Array.from(document.querySelectorAll('#category-list-right .cat-chk:checked')).map(cb=>cb.value);
  const container = document.getElementById('cards');
  const filtered = ITEMS.filter(it=>{
    const cats = Array.isArray(it.category) ? it.category : [it.category];
    const leftOk = leftChecked.length === 0 ? true : cats.some(c=> leftChecked.includes(c));
    const rightOk = rightChecked.length === 0 ? true : cats.some(c=> rightChecked.includes(c));
    const inText = (it.title+" "+it.description).toLowerCase().includes(q);
    return leftOk && rightOk && inText;
  });
  container.innerHTML = '';
  filtered.forEach(i=>container.appendChild(createCard(i)));
  // show no-results message
  let no = document.getElementById('no-results');
  if (!no) {
    no = document.createElement('div');
    no.id = 'no-results';
    no.style.cssText = 'display:none; text-align:center; padding:2em; color:#7c5c2b; font-weight:bold;';
    container.parentNode.insertBefore(no, container.nextSibling);
  }
  if (filtered.length === 0) {
    no.style.display = '';
    no.textContent = 'რეზულტატი ვერ მოიძებნა';
  } else {
    no.style.display = 'none';
    no.textContent = '';
  }
}

document.addEventListener('DOMContentLoaded', async ()=>{
  ITEMS = await fetchData();
  renderCategories(ITEMS);
  // default select all
  document.querySelector('#category-list a[data-cat="all"]').classList.add('active');
  const s = document.getElementById('search');
  if (s) s.addEventListener('input', function(){
    applyFilters();
  });
  applyFilters();
});
