<script lang="ts">
	import favicon from '$lib/assets/favicon.svg';
	import { ModeWatcher } from 'mode-watcher';
	import '../app.css';
	import '@fontsource-variable/bricolage-grotesque';

	let { children } = $props();
</script>

<svelte:head>
	<link rel="icon" href={favicon} />
	<title>Voz Cívica</title>
</svelte:head>

<ModeWatcher />
{@render children()}
