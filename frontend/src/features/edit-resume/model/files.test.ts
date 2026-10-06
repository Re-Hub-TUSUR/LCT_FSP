import { describe, expect, it } from 'vitest'
import { photoFileError, resumeFileError } from './files'

function file(name: string, bytes: number[]) {
  return new File([new Uint8Array(bytes)], name)
}

describe('resume files', () => {
  it('accepts a PDF and a DOCX and refuses everything else', async () => {
    expect(await resumeFileError(file('cv.pdf', [0x25, 0x50, 0x44, 0x46, 0x2d]))).toBeNull()
    const docx = [0x50, 0x4b, 0x03, 0x04, ...new TextEncoder().encode('word/')]
    expect(await resumeFileError(file('cv.docx', docx))).toBeNull()
    expect(await resumeFileError(file('cv.exe', [0x25, 0x50, 0x44, 0x46]))).toMatch(/PDF или DOCX/)
    expect(await resumeFileError(file('cv.pdf.exe', [0x25, 0x50, 0x44, 0x46]))).toMatch(
      /PDF или DOCX/,
    )
    expect(await resumeFileError(file('notes.pdf', [0x00, 0x01, 0x02, 0x03]))).toMatch(/не PDF/)
    expect(await resumeFileError(file('sheet.docx', [0x50, 0x4b, 0x03, 0x04, 0x00]))).toMatch(
      /не документ DOCX/,
    )
  })

  it('accepts a real image header and refuses svg', async () => {
    const png = [0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a, 0, 0]
    expect(await photoFileError(file('face.png', png))).toBeNull()
    expect(await photoFileError(file('face.jpg', [0xff, 0xd8, 0xff, 0xe0]))).toBeNull()
    const svg = [...new TextEncoder().encode('<svg></svg>')]
    expect(await photoFileError(file('face.svg', svg))).toMatch(/JPEG, PNG или WebP/)
    expect(await photoFileError(file('face.png', svg))).toMatch(/не похоже на фотографию/)
  })
})
