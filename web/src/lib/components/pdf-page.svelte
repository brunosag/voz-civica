<script lang="ts">
	import type { PDFDocumentProxy } from 'pdfjs-dist';
	import { PdfPageRenderer } from './pdf-page-renderer.svelte';

	interface Props {
		pdfDoc: PDFDocumentProxy;
		pageNum: number;
		searchStrings?: string[];
	}

	let { pdfDoc, pageNum, searchStrings = [] }: Props = $props();
	let canvas: HTMLCanvasElement | undefined = $state();
	let textLayer: HTMLDivElement | undefined = $state();

	$effect(() => {
		if (pdfDoc && canvas && textLayer) {
			const renderer = new PdfPageRenderer(pdfDoc, pageNum);
			renderer.render(canvas, textLayer, searchStrings);
		}
	});
</script>

<div class="relative mb-4 inline-block shadow-md">
	<canvas bind:this={canvas} class="block"></canvas>
	<div bind:this={textLayer} class="absolute inset-0 overflow-hidden leading-none"></div>
</div>
