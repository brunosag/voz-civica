<script lang="ts">
	import { page } from '$app/state';
	import PdfViewer from '$lib/components/pdf-viewer.svelte';
</script>

<div>{page.params.id}</div>

<PdfViewer
	pdfUrl="pl_example.pdf"
	searchStrings={[
		'necessidade de que seja estabelecido como direito do cidadão que vai a eventos em Porto Alegre, por meio de Lei Municipal, o acesso à água potável para consumo',
		'no verão, as temperaturas observadas são altíssimas',
		'dos estabelecimentos referidos no caput deste artigo'
	]}
/>
