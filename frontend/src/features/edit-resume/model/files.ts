export const RESUME_LIMIT = 5 * 1024 * 1024
export const PHOTO_LIMIT = 2 * 1024 * 1024

const PHOTO_EXT = new Set(['jpg', 'jpeg', 'png', 'webp'])

function extension(name: string): string {
  const base = name.split(/[/\\]/).pop() ?? ''
  const dot = base.lastIndexOf('.')
  return dot === -1 ? '' : base.slice(dot + 1).toLowerCase()
}

async function head(file: File, size: number): Promise<Uint8Array> {
  return new Uint8Array(await file.slice(0, size).arrayBuffer())
}

/** Resume attachment: only PDF and DOCX, and the bytes must match the extension. */
export async function resumeFileError(file: File): Promise<string | null> {
  const ext = extension(file.name)
  if (ext !== 'pdf' && ext !== 'docx') {
    return 'Нужен файл PDF или DOCX. Другие форматы не принимаются.'
  }
  if (file.size <= 0) return 'Файл пустой.'
  if (file.size > RESUME_LIMIT) return 'Файл больше 5 МБ. Сожмите его или заполните поля вручную.'

  const bytes = await head(file, ext === 'pdf' ? 5 : 80_000)
  if (ext === 'pdf') {
    const pdf = bytes[0] === 0x25 && bytes[1] === 0x50 && bytes[2] === 0x44 && bytes[3] === 0x46
    if (!pdf) return 'Это не PDF. Проверьте файл и приложите его ещё раз.'
    return null
  }
  const zip = bytes[0] === 0x50 && bytes[1] === 0x4b && bytes[2] === 0x03 && bytes[3] === 0x04
  const word = new TextDecoder('latin1').decode(bytes).includes('word/')
  if (!zip || !word) return 'Это не документ DOCX. Проверьте файл и приложите его ещё раз.'
  return null
}

/** The portrait the server found in the resume file (base64 JPEG) as a file for the photo upload. */
export function draftPhotoFile(base64: string): File | null {
  try {
    const bytes = Uint8Array.from(atob(base64), (char) => char.charCodeAt(0))
    return new File([bytes], 'resume-photo.jpg', { type: 'image/jpeg' })
  } catch {
    return null
  }
}

/** Profile photo: JPEG, PNG or WebP, and the header must match. SVG and HTML are refused. */
export async function photoFileError(file: File): Promise<string | null> {
  const ext = extension(file.name)
  if (!PHOTO_EXT.has(ext)) return 'Нужна фотография JPEG, PNG или WebP.'
  if (file.size <= 0) return 'Файл пустой.'
  if (file.size > PHOTO_LIMIT) return 'Фото больше 2 МБ. Сожмите его и попробуйте ещё раз.'

  const bytes = await head(file, 12)
  const jpeg = bytes[0] === 0xff && bytes[1] === 0xd8 && bytes[2] === 0xff
  const png =
    bytes[0] === 0x89 &&
    bytes[1] === 0x50 &&
    bytes[2] === 0x4e &&
    bytes[3] === 0x47 &&
    bytes[4] === 0x0d &&
    bytes[5] === 0x0a &&
    bytes[6] === 0x1a &&
    bytes[7] === 0x0a
  const webp =
    bytes[0] === 0x52 &&
    bytes[1] === 0x49 &&
    bytes[2] === 0x46 &&
    bytes[3] === 0x46 &&
    bytes[8] === 0x57 &&
    bytes[9] === 0x45 &&
    bytes[10] === 0x42 &&
    bytes[11] === 0x50
  if (!jpeg && !png && !webp) return 'Содержимое файла не похоже на фотографию.'
  return null
}
