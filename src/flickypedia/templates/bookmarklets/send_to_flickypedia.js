/* This bookmarklet opens the "select photos" screen in Flickypedia.
 *
 * If you run it on a non-Flickr page, you get an alert rather than
 * being redirected to a broken page.
 */

const thisUrl = document.location.href;

if (!thisUrl.startsWith('https://www.flickr.com/')) {
  alert("This URL doesn’t live on Flickr.com");
} else {
  open(`{{ base_url }}{{ url_for('select_photos', flickr_url='URL') | replace('URL', '${document.location.href}') }}`, "targetname");
}




