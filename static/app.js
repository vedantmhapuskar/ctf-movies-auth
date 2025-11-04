document.addEventListener('DOMContentLoaded', ()=>{
  const ma = document.getElementById('moviesArea');
  if(ma){
    fetch('/api/movies').then(r=>r.json()).then(j=>{
      const ul = document.createElement('ul');
      j.forEach(m=>{
        const li = document.createElement('li');
        const a = document.createElement('a');
        a.href = `/movie?movieID=${encodeURIComponent(m.id)}`;
        a.textContent = `${m.id} - ${m.title}`;
        li.appendChild(a);
        ul.appendChild(li);
      });
      ma.innerHTML = '';
      ma.appendChild(ul);
    }).catch(e=>{ ma.textContent = 'Failed to load movies'; });
  }
});
