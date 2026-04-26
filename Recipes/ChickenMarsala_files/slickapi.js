const fb = document.querySelector('.postdiv .sticky-share-wrapper .save a');
 
async function ensureSlickstream() {
   if (window.slickstream) {
       return window.slickstream.v1;
   }
   return new Promise((resolve, reject) => {
      document.addEventListener('slickstream-ready', () => {
         resolve(window.slickstream.v1);
      });
   }); 
}
 
async function updateFavoriteButtonState() {
   const slickstream = await ensureSlickstream();
   const isFavorite = slickstream.favorites.getState();
   fb.textContent = slickstream.favorites.getState() ? fb.getAttribute('data-saved') : fb.getAttribute('data-unsaved');
}
 
async function favoriteButtonClick() {
   const slickstream = await ensureSlickstream();
   const state = slickstream.favorites.getState();
   slickstream.favorites.setState(!state);
}
fb.addEventListener('click',function(e) {
   e.preventDefault();
   favoriteButtonClick();
});
 
document.addEventListener('slickstream-favorite-change', () => {
  updateFavoriteButtonState();
});
 
updateFavoriteButtonState();