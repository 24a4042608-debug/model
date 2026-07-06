/**
 * Converts Vietnamese accented characters to their basic English equivalents.
 * Useful for slug generation.
 */
export function removeVietnameseAccents(str: string): string {
  let acc = str;
  acc = acc.replace(/à|á|ạ|ả|ã|â|ầ|ấ|ậ|ẩ|ẫ|ă|ằ|ắ|ặ|ẳ|ẵ/g, "a");
  acc = acc.replace(/è|é|ẹ|ẻ|ẽ|ê|ề|ế|ệ|ể|ễ/g, "e");
  acc = acc.replace(/ì|í|ị|ỉ|ĩ/g, "i");
  acc = acc.replace(/ò|ó|ọ|ỏ|õ|ô|ồ|ố|ộ|ổ|ỗ|ơ|ờ|ớ|ợ|ở|ỡ/g, "o");
  acc = acc.replace(/ù|ú|ụ|ủ|ũ|ư|ừ|ứ|ự|ử|ữ/g, "u");
  acc = acc.replace(/ỳ|ý|ỵ|ỷ|ỹ/g, "y");
  acc = acc.replace(/đ/g, "d");
  acc = acc.replace(/À|Á|Ạ|Ả|Ã|Â|Ầ|Ấ|Ậ|Ẩ|Ẫ|Ă|Ằ|Ắ|Ặ|Ẳ|Ẵ/g, "A");
  acc = acc.replace(/È|É|Ẹ|Ẻ|Ẽ|Ê|Ề|Ế|Ệ|Ể|Ễ/g, "E");
  acc = acc.replace(/Ì|Í|Ị|Ỉ|Ĩ/g, "I");
  acc = acc.replace(/Ò|Ó|Ọ|Ỏ|Õ|Ô|Ồ|Ố|Ộ|Ổ|Ỗ|Ơ|Ờ|Ớ|Ợ|Ở|Ỡ/g, "O");
  acc = acc.replace(/Ù|Ú|Ụ|Ủ|Ũ|Ư|Ừ|Ứ|Ự|Ử|Ữ/g, "U");
  acc = acc.replace(/Ỳ|Ý|Ỵ|Ỷ|Ỹ/g, "Y");
  acc = acc.replace(/Đ/g, "D");
  // Combine accents
  acc = acc.normalize("NFD").replace(/[\u0300-\u036f]/g, "");
  return acc;
}

/**
 * Generates an SEO friendly slug from a Vietnamese string.
 */
export function generateSlug(str: string): string {
  const noAccents = removeVietnameseAccents(str);
  return noAccents
    .toLowerCase()
    .trim()
    .replace(/[^\w\s-]/g, "") // remove non-word, non-space, non-hyphen chars
    .replace(/[\s_]+/g, "-")  // replace spaces and underscores with hyphens
    .replace(/-+/g, "-")      // collapse consecutive hyphens
    .replace(/^-+|-+$/g, ""); // remove leading/trailing hyphens
}
