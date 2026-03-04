const upcomingBody = document.getElementById('upcomingBody');
const cancelledBody = document.getElementById('cancelledBody');
const propertyFilter = document.getElementById('propertyFilter');
const daysFilter = document.getElementById('daysFilter');
const refreshBtn = document.getElementById('refreshBtn');

function row(cols) {
  const tr = document.createElement('tr');
  cols.forEach((c) => {
    const td = document.createElement('td');
    td.textContent = c ?? '';
    tr.appendChild(td);
  });
  return tr;
}

function fill(tbody, items, cancelled = false) {
  tbody.innerHTML = '';
  if (!items.length) {
    tbody.appendChild(row(['—', 'No records', '—', '—', '—']));
    return;
  }
  items.forEach((i) => {
    tbody.appendChild(
      row(
        cancelled
          ? [i.arrival_date, i.property_name, i.guest_name, i.package_name, i.cancelled_at]
          : [i.arrival_date, i.property_name, i.guest_name, i.package_name, i.status]
      )
    );
  });
}

async function loadData() {
  const property = propertyFilter.value;
  const days = daysFilter.value || '14';

  const [upcomingRes, cancelledRes] = await Promise.all([
    fetch(`/api/packages/upcoming?property=${property}&days=${days}`),
    fetch(`/api/packages/cancelled?property=${property}&days=${days}`),
  ]);

  const upcoming = await upcomingRes.json();
  const cancelled = await cancelledRes.json();
  fill(upcomingBody, upcoming.items || []);
  fill(cancelledBody, cancelled.items || [], true);
}

refreshBtn.addEventListener('click', loadData);
propertyFilter.addEventListener('change', loadData);
daysFilter.addEventListener('change', loadData);

loadData();
setInterval(loadData, 60000);
