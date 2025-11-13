import json
from contextlib import contextmanager

from django.core.management.base import BaseCommand
from django.db import DatabaseError, transaction

from apps.cart.models import Cart, CartItem
from apps.orders.models import Order, OrderStatus
from apps.products.models import Product


class Command(BaseCommand):
    help = "Ejecuta EXPLAIN sobre consultas críticas para validar el uso de índices."

    def handle(self, *args, **options):
        self.stdout.write(self.style.MIGRATE_HEADING("Analizando índices con EXPLAIN...\n"))

        with self.sample_data() as context:
            scenarios = [
                ("Listado productos activos por fecha de creación",
                 Product.objects.filter(active=True).order_by("-created_at")),
                ("Búsqueda por prefijo (name__istartswith='a')",
                 Product.objects.filter(name__istartswith="a")),
                ("Ítems de carrito por cart/product",
                 CartItem.objects.filter(
                     cart_id=context["cart"].id,
                     product_id__in=[context["product"].id],
                 )),
                ("Órdenes por correo demo@example.com",
                 Order.objects.filter(customer_email="demo@example.com")),
            ]

            for title, qs in scenarios:
                self.stdout.write(self.style.NOTICE(f"\n{title}"))
                self.stdout.write(self.style.SQL_COLTYPE(str(qs.query)))
                plan, fmt, raw_plan = self._explain(qs)
                self.stdout.write(self.style.HTTP_INFO(f"Formato EXPLAIN: {fmt}"))
                if not plan:
                    self.stdout.write(self.style.WARNING("No se pudieron obtener detalles del plan estructurado."))
                    if raw_plan:
                        self.stdout.write(raw_plan)
                    continue
                for row in plan:
                    self.stdout.write(
                        "  tabla={table} | key={key} | type={type} | rows={rows} | extra={extra}".format(
                            table=row.get("table"),
                            key=row.get("key"),
                            type=row.get("type"),
                            rows=row.get("rows"),
                            extra=row.get("extra") or "",
                        )
                    )
                if fmt == "TEXT" and raw_plan:
                    self.stdout.write(raw_plan)

    def _explain(self, qs):
        raw_plan = ""
        try:
            json_plan = qs.explain(format="JSON")
            data = json.loads(json_plan)
            rows = []
            self._extract_json_plan(data, rows)
            if rows:
                return rows, "JSON", json_plan
        except DatabaseError as exc:
            self.stderr.write(self.style.WARNING(f"EXPLAIN JSON no disponible: {exc}"))

        try:
            text_plan = qs.explain()
            raw_plan = text_plan
        except DatabaseError as exc:
            self.stderr.write(self.style.ERROR(f"EXPLAIN falló: {exc}"))
            return [], "ERROR", raw_plan

        rows = self._parse_text_plan(text_plan)
        return rows, "TEXT", raw_plan

    def _extract_json_plan(self, node, collection):
        if isinstance(node, dict):
            if "table_name" in node:
                extra_parts = []
                for extra_key in (
                    "attached_condition",
                    "attached_subqueries",
                    "using_temporary_table",
                    "using_filesort",
                ):
                    value = node.get(extra_key)
                    if not value:
                        continue
                    if isinstance(value, str):
                        extra_parts.append(value)
                    elif isinstance(value, list):
                        extra_parts.extend(str(item) for item in value)
                    elif value is True:
                        extra_parts.append(extra_key)
                collection.append(
                    {
                        "table": node.get("table_name"),
                        "key": node.get("key"),
                        "type": node.get("access_type"),
                        "rows": node.get("rows_examined_per_scan")
                        or node.get("rows_produced_per_join")
                        or node.get("rows"),
                        "extra": "; ".join(extra_parts),
                    }
                )
            for value in node.values():
                self._extract_json_plan(value, collection)
        elif isinstance(node, list):
            for item in node:
                self._extract_json_plan(item, collection)

    def _parse_text_plan(self, plan_text):
        lines = [line.rstrip() for line in plan_text.strip().splitlines() if line.strip()]
        rows = []
        headers = None
        for line in lines:
            line = line.rstrip()
            if line.startswith("+") and line.endswith("+"):
                continue
            if line.startswith("|") and line.endswith("|"):
                parts = [part.strip() for part in line.split("|")[1:-1]]
                if headers is None:
                    headers = parts
                    continue
                if headers and parts:
                    data = dict(zip(headers, parts))
                    rows.append(
                        {
                            "table": data.get("table") or data.get("Table"),
                            "key": data.get("key") or data.get("possible_keys"),
                            "type": data.get("type"),
                            "rows": data.get("rows"),
                            "extra": data.get("Extra"),
                        }
                    )
        if rows:
            return rows

        lines = [line.strip() for line in lines if not line.startswith("+")]
        if len(lines) < 2:
            return []
        headers = self._split_columns(lines[0])
        for line in lines[1:]:
            values = self._split_columns(line)
            data = dict(zip(headers, values))
            rows.append(
                {
                    "table": data.get("table") or data.get("Table"),
                    "key": data.get("key") or data.get("possible_keys"),
                    "type": data.get("type"),
                    "rows": data.get("rows"),
                    "extra": data.get("Extra"),
                }
            )
        return rows

    @staticmethod
    def _split_columns(line):
        parts = [part for part in line.split("\t") if part]
        if len(parts) <= 1:
            import re
            parts = [part for part in re.split(r"\s{2,}", line) if part]
        return parts

    @contextmanager
    def sample_data(self):
        created = []
        with transaction.atomic():
            product = Product.objects.filter(active=True).order_by("-created_at").first()
            if not product:
                product = Product.objects.create(
                    name="Producto Índice",
                    slug="producto-indice",
                    price=19990,
                    stock_qty=50,
                    active=True,
                )
                created.append(product)

            prefix_product = Product.objects.filter(name__istartswith="a").first()
            if not prefix_product:
                prefix_product = Product.objects.create(
                    name="Alfombra Índice",
                    slug="alfombra-indice",
                    price=25990,
                    stock_qty=20,
                    active=True,
                )
                created.append(prefix_product)

            cart = Cart.objects.filter(items__isnull=False).first()
            if not cart:
                cart = Cart.objects.create(session_token="analyze-session", is_active=True)
                created.append(cart)
            cart_item = cart.items.first()
            if not cart_item:
                cart_item = CartItem.objects.create(
                    cart=cart,
                    product=product,
                    quantity=1,
                    unit_price=product.final_price,
                    total_price=product.final_price,
                )
                created.append(cart_item)

            order = Order.objects.filter(customer_email="demo@example.com").first()
            if not order:
                status, _ = OrderStatus.objects.get_or_create(
                    code="PENDING", defaults={"description": "Pendiente"}
                )
                order = Order.objects.create(
                    status=status,
                    customer_name="Demo Customer",
                    customer_email="demo@example.com",
                    customer_phone="",
                    shipping_street="Calle Demo 123",
                    shipping_city="Santiago",
                    shipping_region="Metropolitana",
                    shipping_postal_code="8320000",
                    total_amount=product.final_price,
                    shipping_cost=0,
                )
                created.append(order)

            context = {
                "product": product,
                "prefix_product": prefix_product,
                "cart": cart,
                "cart_item": cart_item,
                "order": order,
            }
            try:
                yield context
            finally:
                for obj in reversed(created):
                    obj.delete()

