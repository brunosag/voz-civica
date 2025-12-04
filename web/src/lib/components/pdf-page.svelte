<script lang="ts">
	import type { PDFPageProxy } from 'pdfjs-dist';
	import 'pdfjs-dist/web/pdf_viewer.css';
	import { TextLayerBuilder } from 'pdfjs-dist/web/pdf_viewer.mjs';
	import { resource } from 'runed';

	let { page, searchStrings = [] }: { page: PDFPageProxy; searchStrings?: string[] } = $props();

	let containerEl: HTMLDivElement | undefined = $state();
	let canvasEl: HTMLCanvasElement | undefined = $state();
	let containerWidth: number | undefined = $state();

	const render = async (canvas: HTMLCanvasElement, container: HTMLDivElement, width: number) => {
		const baseWidth = page.getViewport({ scale: 1 }).width;
		const scale = width / baseWidth;
		const viewport = page.getViewport({ scale });
		canvas.height = viewport.height;
		canvas.width = viewport.width;
		await page.render({ canvas, viewport }).promise;

		const textLayerBuilder = new TextLayerBuilder({ pdfPage: page });
		await textLayerBuilder.render({ viewport });
		textLayerBuilder.div.style.setProperty('--total-scale-factor', String(scale));
		container.appendChild(textLayerBuilder.div);
	};

	const renderingResource = resource(
		() => containerWidth,
		async () => {
			if (canvasEl && containerEl && containerWidth) {
				await render(canvasEl, containerEl, containerWidth);
			}
		},
		{ debounce: 300 }
	);
</script>

<div bind:this={containerEl} bind:clientWidth={containerWidth} class="relative w-full">
	<canvas bind:this={canvasEl}></canvas>
</div>
