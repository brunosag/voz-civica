<script lang="ts">
	import favicon from '$lib/assets/favicon.svg';
	import '@fontsource-variable/bricolage-grotesque';
	import '../app.css';

	let { children } = $props();
</script>

<svelte:head>
	<link rel="icon" href={favicon} />
	<title>Voz Cívica</title>
</svelte:head>

<div class="mx-auto flex h-screen max-w-400 flex-col overflow-hidden px-6">
	<header class="flex items-center justify-between py-8">
		<h1 class="flex items-end gap-2.5">
			<span class="text-3xl font-bold tracking-tighter">Voz Cívica</span>
			<span class="hidden"> — </span>
			<span class="text-xl font-light text-gray-400">Porto Alegre</span>
		</h1>
	</header>
	<main class="min-h-0 grow">
		{@render children()}
	</main>
</div>
