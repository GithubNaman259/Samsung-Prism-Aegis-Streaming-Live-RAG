import re

with open(r'aegis/aegis/backend/pipeline.py', 'r', encoding='utf-8') as f:
    content = f.read()

old_block = '''        if venue_queries:
            reusable = self._reuse_provisional(ctx, venue_queries)
            reused_count += len(reusable)
            to_search = [sq.text for sq in venue_queries if sq.text not in reusable]
            fresh = await self.engine.search_many(to_search)
            results.extend(reusable.values())
            results.extend(fresh)'''

new_block = '''        if venue_queries:
            reusable = {} if is_refine else self._reuse_provisional(ctx, venue_queries)
            reused_count += len(reusable)
            to_search = [sq.text for sq in venue_queries if sq.text not in reusable]
            fresh = await self.engine.search_many(to_search)
            results.extend(reusable.values())
            results.extend(fresh)'''

if old_block in content:
    content = content.replace(old_block, new_block)
    print("Patched venue_queries reuse")
else:
    print("Failed to find venue_queries reuse")

old_block2 = '''        reusable = self._reuse_provisional(ctx, other_queries)
        reused_count += len(reusable)
        to_search = [sq.text for sq in other_queries if sq.text not in reusable]
        fresh = await self.engine.search_many(to_search)
        results.extend(reusable.values())
        results.extend(fresh)'''

new_block2 = '''        reusable = {} if is_refine else self._reuse_provisional(ctx, other_queries)
        reused_count += len(reusable)
        to_search = [sq.text for sq in other_queries if sq.text not in reusable]
        fresh = await self.engine.search_many(to_search)
        results.extend(reusable.values())
        results.extend(fresh)'''

if old_block2 in content:
    content = content.replace(old_block2, new_block2)
    print("Patched other_queries reuse")
else:
    print("Failed to find other_queries reuse")

with open(r'aegis/aegis/backend/pipeline.py', 'w', encoding='utf-8') as f:
    f.write(content)
