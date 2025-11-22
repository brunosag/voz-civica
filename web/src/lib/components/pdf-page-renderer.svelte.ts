import type { PDFDocumentProxy, PDFPageProxy, PageViewport } from 'pdfjs-dist';
import type { TextItem } from 'pdfjs-dist/types/src/display/api';
import { TextLayerBuilder } from 'pdfjs-dist/web/pdf_viewer.mjs';

interface CharMapEntry {
	item: TextItem;
	index: number;
}

interface HighlightRange {
	item: TextItem;
	start: number;
	end: number;
}

export class PdfPageRenderer {
	constructor(
		private pdfDoc: PDFDocumentProxy,
		private pageNum: number
	) {}

	async render(canvas: HTMLCanvasElement, textLayer: HTMLDivElement, searchStrings: string[] = []) {
		try {
			const page = await this.pdfDoc.getPage(this.pageNum);
			const viewport = page.getViewport({ scale: 1.5 });

			this.#setupCanvas(canvas, viewport);
			this.#setupTextLayer(textLayer, viewport);

			const ctx = canvas.getContext('2d');
			if (!ctx) return;

			// Render base layer
			await page.render({ canvas, viewport }).promise;

			// Render text layer
			const textLayerBuilder = new TextLayerBuilder({
				pdfPage: page
			});
			await textLayerBuilder.render({ viewport });
			textLayer.appendChild(textLayerBuilder.div);

			// Apply highlights
			if (searchStrings.length > 0) {
				await this.#highlightMatches(page, ctx, viewport, searchStrings);
			}
		} catch (err) {
			console.error(`PDF Render Error (Page ${this.pageNum}):`, err);
		}
	}

	#setupCanvas(canvas: HTMLCanvasElement, viewport: PageViewport) {
		canvas.height = viewport.height;
		canvas.width = viewport.width;
	}

	#setupTextLayer(textLayer: HTMLDivElement, viewport: PageViewport) {
		textLayer.style.width = `${viewport.width}px`;
		textLayer.style.height = `${viewport.height}px`;
		textLayer.style.setProperty('--scale-factor', '1.5');
		textLayer.innerHTML = '';
	}

	async #highlightMatches(
		page: PDFPageProxy,
		ctx: CanvasRenderingContext2D,
		viewport: PageViewport,
		terms: string[]
	) {
		const textContent = await page.getTextContent();
		const items = textContent.items.filter((item): item is TextItem => 'str' in item);

		const { fullText, charMap } = this.#buildCharMap(items);
		const fullTextLower = fullText.toLowerCase();

		ctx.save();
		ctx.globalCompositeOperation = 'multiply';
		ctx.fillStyle = 'rgb(255, 255, 0)';

		for (const term of terms) {
			const termLower = term.toLowerCase();
			if (!termLower) continue;

			let matchIdx = fullTextLower.indexOf(termLower);
			while (matchIdx !== -1) {
				const ranges = this.#getHighlightRanges(matchIdx, matchIdx + term.length, charMap);

				for (let i = 0; i < ranges.length; i++) {
					this.#drawHighlightRect(ctx, viewport, ranges[i], ranges[i + 1]);
				}

				matchIdx = fullTextLower.indexOf(termLower, matchIdx + 1);
			}
		}
		ctx.restore();
	}

	#buildCharMap(items: TextItem[]) {
		let fullText = '';
		const charMap: (CharMapEntry | null)[] = [];

		for (const item of items) {
			for (let i = 0; i < item.str.length; i++) {
				const char = item.str[i];
				// Avoid double spaces if the text already ends with one
				if (char === ' ' && fullText.endsWith(' ')) {
					continue;
				}
				fullText += char;
				charMap.push({ item, index: i });
			}
			// Virtual space for word breaks/line endings
			if (!fullText.endsWith(' ')) {
				fullText += ' ';
				charMap.push(null);
			}
		}
		return { fullText, charMap };
	}

	#getHighlightRanges(start: number, end: number, charMap: (CharMapEntry | null)[]) {
		const ranges: HighlightRange[] = [];
		let current: HighlightRange | null = null;

		for (let i = start; i < end; i++) {
			const entry = charMap[i];
			if (!entry) continue; // Skip virtual spaces

			if (!current || current.item !== entry.item) {
				if (current) ranges.push(current);
				current = { item: entry.item, start: entry.index, end: entry.index + 1 };
			} else {
				current.end = entry.index + 1;
			}
		}
		if (current) ranges.push(current);
		return ranges;
	}

	#drawHighlightRect(
		ctx: CanvasRenderingContext2D,
		viewport: PageViewport,
		range: HighlightRange,
		nextRange?: HighlightRange
	) {
		const { item, start, end } = range;
		const tx = item.transform;
		const fontHeight = Math.sqrt(tx[2] * tx[2] + tx[3] * tx[3]);

		ctx.font = `${fontHeight}px sans-serif`;
		const totalMeas = ctx.measureText(item.str).width;
		const scale = totalMeas > 0 ? item.width / totalMeas : 0;

		const widthBefore = ctx.measureText(item.str.substring(0, start)).width * scale;
		const widthMatch = ctx.measureText(item.str.substring(start, end)).width * scale;

		const x = tx[4] + widthBefore;
		const y = tx[5];
		let width = widthMatch;

		// Check if we should extend to the next range (fill gap)
		if (nextRange && Math.abs(nextRange.item.transform[5] - y) < 1) {
			const nextTx = nextRange.item.transform;
			const nextFontHeight = Math.sqrt(nextTx[2] * nextTx[2] + nextTx[3] * nextTx[3]);

			ctx.font = `${nextFontHeight}px sans-serif`;
			const nextTotalMeas = ctx.measureText(nextRange.item.str).width;
			const nextScale = nextTotalMeas > 0 ? nextRange.item.width / nextTotalMeas : 0;
			const nextWidthBefore =
				ctx.measureText(nextRange.item.str.substring(0, nextRange.start)).width * nextScale;

			const nextX = nextTx[4] + nextWidthBefore;

			if (nextX > x + width) {
				width = nextX - x;
			}
		}

		const rect = viewport.convertToViewportRectangle([
			x,
			y - fontHeight * 0.25,
			x + width,
			y + fontHeight * 1.05
		]);

		const minX = Math.min(rect[0], rect[2]);
		const minY = Math.min(rect[1], rect[3]);
		const w = Math.abs(rect[2] - rect[0]);
		const h = Math.abs(rect[3] - rect[1]);

		ctx.fillRect(minX, minY, w, h);
	}
}
