<script module lang="ts">
	import * as pdfjs from 'pdfjs-dist';
	import pdfWorker from 'pdfjs-dist/build/pdf.worker.min.mjs?url';

	if (typeof window !== 'undefined' && 'Worker' in window) {
		pdfjs.GlobalWorkerOptions.workerSrc = pdfWorker;
	}
</script>

<script lang="ts">
	import 'pdfjs-dist/web/pdf_viewer.css';
	import { ElementSize, resource } from 'runed';
	import PdfPage from './pdf-page.svelte';

	let { src, searchStrings = [] }: { src: string; searchStrings?: string[] } = $props();

	let containerEl = $state() as HTMLElement;
	let size = new ElementSize(() => containerEl);

	const pdf = resource(
		() => src,
		async (url) => pdfjs.getDocument(`api/pdf?url=${url}`).promise
	);
</script>

<div
	bind:this={containerEl}
	class="flex h-full w-full flex-col items-center gap-4 overflow-y-auto bg-gray-100 p-4"
>
	{#if pdf.loading}
		<div class="p-4 text-gray-500">Loading PDF...</div>
	{:else if pdf.error}
		<div class="p-4 text-red-500">Error loading PDF: {pdf.error.message}</div>
	{:else if pdf.current}
		{#each Array.from({ length: pdf.current.numPages }, (_, i) => i + 1) as pageNum}
			{#await pdf.current.getPage(pageNum) then page}
				<PdfPage {page} {searchStrings} />
			{/await}
		{/each}
	{/if}
</div>
