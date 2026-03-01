<script>
  // columns: [{ key, label, render? }]
  // rows: array of objects
  export let columns = [];
  export let rows    = [];
  export let empty   = 'No data.';
</script>

{#if rows.length === 0}
  <div class="empty">{empty}</div>
{:else}
  <div class="table-wrap">
    <table>
      <thead>
        <tr>
          {#each columns as col}
            <th>{col.label}</th>
          {/each}
        </tr>
      </thead>
      <tbody>
        {#each rows as row}
          <tr>
            {#each columns as col}
              <td>
                {#if col.render}
                  {@html col.render(row[col.key], row)}
                {:else}
                  {row[col.key] ?? '—'}
                {/if}
              </td>
            {/each}
          </tr>
        {/each}
      </tbody>
    </table>
  </div>
{/if}

<style>
  .table-wrap { overflow-x: auto; }
  table { width: 100%; border-collapse: collapse; font-size: .875rem; }
  th {
    text-align: left;
    font-size: .72rem;
    text-transform: uppercase;
    letter-spacing: .07em;
    color: var(--muted);
    padding: .5rem .75rem;
    border-bottom: 1px solid var(--border);
    font-weight: 600;
    white-space: nowrap;
  }
  td {
    padding: .6rem .75rem;
    border-bottom: 1px solid var(--border);
    vertical-align: middle;
  }
  tr:last-child td { border-bottom: none; }
  tr:hover td { background: var(--cream); }
  .empty {
    color: var(--muted);
    font-size: .9rem;
    padding: 2rem;
    text-align: center;
  }
</style>
